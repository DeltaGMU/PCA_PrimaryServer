from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from server.lib.data_classes.employee import Employee
from server.lib.data_classes.employee_hours import EmployeeHours
from server.lib.database_manager import get_db_session
import calendar
import datetime


async def get_all_time_sheets_for_report(session: Session = None):
    if session is None:
        session = next(get_db_session())
    try:
        now = datetime.datetime.now()
        days_in_cur_month = calendar.monthrange(now.year, now.month)[1]
        all_employees_hours = {}
        all_employees = session.query(Employee).filter(Employee.EmployeeEnabled == 1).all()
        for employee in all_employees:
            time_sheets = session.query(EmployeeHours).filter(
                EmployeeHours.EmployeeID == employee.EmployeeID,
                EmployeeHours.DateWorked.between(f"{now.year}-{now.month}-1", f"{now.year}-{now.month}-{days_in_cur_month}"),
            ).all()
            total_hours = {
                "work_hours": 0,
                "pto_hours": 0,
                "extra_hours": 0,
            }
            for record in time_sheets:
                total_hours['work_hours'] += record.WorkHours
                total_hours['pto_hours'] += record.PTOHours
                total_hours['extra_hours'] += record.ExtraHours
            all_employees_hours[employee.EmployeeID] = total_hours
        session.commit()
    except IntegrityError as err:
        raise RuntimeError from err
    return all_employees_hours


async def check_time_sheets_submitted(session: Session = None):
    if session is None:
        session = next(get_db_session())

    fully_submitted = []
    not_submitted = []

    now = datetime.datetime.now()
    days_in_cur_month = calendar.monthrange(now.year, now.month)[1]

    all_employees = session.query(Employee).filter(Employee.EmployeeEnabled == 1).all()

    for employee in all_employees:
        matching_records = session.query(EmployeeHours).filter(
            EmployeeHours.EmployeeID == employee.EmployeeID,
            EmployeeHours.DateWorked.between(f"{now.year}-{now.month}-1", f"{now.year}-{now.month}-{days_in_cur_month}")
        ).count()
        if matching_records == days_in_cur_month:
            fully_submitted.append(employee)
        else:
            not_submitted.append(employee)
    session.commit()
    return all_employees, len(fully_submitted), len(not_submitted)
