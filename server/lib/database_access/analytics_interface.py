from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from server.lib.data_classes.employee_role import EmployeeRole
from server.lib.data_classes.employee import Employee
from server.lib.data_classes.employee_hours import EmployeeHours
from server.lib.database_manager import get_db_session
from datetime import datetime


async def get_all_time_sheets_for_report(start_date: str, end_date: str, session: Session = None):
    if session is None:
        session = next(get_db_session())
    try:

        employee_time_sheet_records = session.query(Employee, EmployeeHours, EmployeeRole).filter(
            Employee.EmployeeEnabled == 1,
            EmployeeRole.id == Employee.EmployeeRoleID,
            EmployeeHours.EmployeeID == Employee.EmployeeID,
            EmployeeHours.DateWorked.between(start_date, end_date)
        ).order_by(Employee.FirstName).all()
        if employee_time_sheet_records is None:
            raise RuntimeError("Encountered an error retrieving employee time sheets!")

        all_employees_hours = {}
        for record in employee_time_sheet_records:
            all_employees_hours[record[0].EmployeeID] = {
                "full_name": f"{record[0].FirstName.capitalize()} {record[0].LastName.capitalize()}",
                "work_hours": 0,
                "pto_hours": 0,
                "extra_hours": 0,
                "comments": []
            }

        for record in employee_time_sheet_records:
            all_employees_hours[record[0].EmployeeID]["work_hours"] += record[1].WorkHours
            all_employees_hours[record[0].EmployeeID]["pto_hours"] += record[1].PTOHours
            all_employees_hours[record[0].EmployeeID]["extra_hours"] += record[1].ExtraHours
            if record[1].Comment and len(record[1].Comment) > 0:
                all_employees_hours[record[0].EmployeeID]["comments"].append({"date": datetime.strftime(record[1].DateWorked, '%Y-%m-%d'), "comment": record[1].Comment})

        session.commit()
    except IntegrityError as err:
        raise RuntimeError from err
    return all_employees_hours


async def get_employees_within_reporting_period(start_date: str, end_date: str, session: Session = None):
    if session is None:
        session = next(get_db_session())
    all_employees = session.query(Employee, EmployeeHours).filter(
        Employee.EmployeeEnabled == 1,
        EmployeeHours.EmployeeID == Employee.EmployeeID,
        EmployeeHours.DateWorked.between(start_date, end_date)
    ).all()
    session.commit()
    return all_employees[0]
