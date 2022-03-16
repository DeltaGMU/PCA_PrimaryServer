from __future__ import annotations
from typing import Dict, List
from sqlalchemy.orm import Session
from sqlalchemy.sql.functions import func
from server.lib.utils.date_utils import check_date_formats
from server.lib.data_classes.employee_hours import EmployeeHours, PydanticEmployeeTimesheetSubmission, PydanticEmployeeTimesheetRemoval
from server.lib.database_manager import get_db_session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status


async def create_employee_multiple_hours(employee_id: str, employee_updates: List[PydanticEmployeeTimesheetSubmission], session: Session = None) -> List[EmployeeHours]:
    if session is None:
        session = next(get_db_session())
    if None in (employee_id, *employee_updates):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="One or more provided parameters are invalid! Please check the submitted data.")
    try:
        if not check_date_formats([employee_update.date_worked for employee_update in employee_updates]):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="One or more provided dates are not in the YYYY-MM-DD format!")
        submitted_time_sheets = []
        for timesheet in employee_updates:
            timesheet_submission = EmployeeHours(
                employee_id,
                timesheet.work_hours,
                timesheet.pto_hours,
                timesheet.extra_hours,
                timesheet.date_worked
            )
            try:
                session.add(timesheet_submission)
            except IntegrityError:
                session.query(
                    EmployeeHours
                ).filter(
                    EmployeeHours.EmployeeID == employee_id,
                    EmployeeHours.DateWorked == timesheet.date_worked
                ).update(
                    {
                        EmployeeHours.WorkHours: timesheet.work_hours,
                        EmployeeHours.PTOHours: timesheet.pto_hours,
                        EmployeeHours.ExtraHours: timesheet.extra_hours
                    }
                )
            submitted_time_sheets.append(timesheet_submission)
        session.commit()
    except IntegrityError as err:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
    return submitted_time_sheets


async def create_employee_hours(employee_id: str, date_worked: str, work_hours: int, pto_hours: int = 0, extra_hours: int = 0, session: Session = None) -> EmployeeHours:
    if session is None:
        session = next(get_db_session())
    if None in (employee_id, date_worked, work_hours, pto_hours, extra_hours):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="One or more provided parameters are invalid! Please check the submitted data.")
    try:
        if not check_date_formats(date_worked):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="One or more provided dates are not in the YYYY-MM-DD format!")
        timesheet_exists = session.query(EmployeeHours).filter(
            EmployeeHours.EmployeeID == employee_id,
            EmployeeHours.DateWorked == date_worked
        ).all()
        if len(timesheet_exists) == 0:
            timesheet_submission = EmployeeHours(
                employee_id,
                work_hours,
                pto_hours,
                extra_hours,
                date_worked
            )
            session.add(timesheet_submission)
            session.commit()
        else:
            session.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Duplicate date entry! The employee already has hours entered for this day! You can update this entry instead using an UPDATE request.")
    except IntegrityError as err:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
    return timesheet_submission


async def update_employee_hours(employee_id: str, date_worked: str, work_hours: int = 0, pto_hours: int = 0, extra_hours: int = 0, session: Session = None) -> EmployeeHours:
    if session is None:
        session = next(get_db_session())
    try:
        session.query(
            EmployeeHours
        ).filter(
            EmployeeHours.EmployeeID == employee_id,
            EmployeeHours.DateWorked == date_worked
        ).update(
            {
                EmployeeHours.WorkHours: work_hours,
                EmployeeHours.PTOHours: pto_hours,
                EmployeeHours.ExtraHours: extra_hours
            }
        )
        session.commit()
        updated_hours = session.query(
            EmployeeHours
        ).filter(
            EmployeeHours.EmployeeID == employee_id,
            EmployeeHours.DateWorked == date_worked
        ).first()
        if updated_hours is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="The employee timesheet information could not be updated for the provided date. "
                                       "Please check the provided information for errors!")
    except IntegrityError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
    return updated_hours


async def delete_all_employee_time_sheets(employee_id: str, session: Session = None):
    deletion_task = session.query(EmployeeHours).filter(
        EmployeeHours.EmployeeID == employee_id.strip()
    ).all().delete()
    session.commit()
    if deletion_task != 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not successfully remove all employee time sheets!")


async def delete_employee_time_sheets(employee_id: str, dates_worked: PydanticEmployeeTimesheetRemoval, session: Session = None) -> List[EmployeeHours]:
    if isinstance(dates_worked, PydanticEmployeeTimesheetRemoval):
        dates_worked = dates_worked.dates_worked
        if dates_worked is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provided request body did not contain any valid work dates!")
    removed_employee_time_sheets: List[EmployeeHours] = []
    if isinstance(dates_worked, List):
        time_sheets = session.query(EmployeeHours).filter(
            EmployeeHours.EmployeeID == employee_id.strip(),
            EmployeeHours.DateWorked.in_(dates_worked)).all()
        if time_sheets:
            for time_sheet in time_sheets:
                session.delete(time_sheet)
                removed_employee_time_sheets.append(time_sheet)
            session.commit()
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot remove employee time sheets that do not exist in the database!")
    else:
        time_sheet = session.query(EmployeeHours).filter(
            EmployeeHours.EmployeeID == employee_id.strip(),
            EmployeeHours.DateWorked == dates_worked.strip()
        ).first()
        if time_sheet:
            session.delete(time_sheet)
            removed_employee_time_sheets.append(time_sheet)
            session.commit()
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot remove an employee time sheet that does not exist in the database!")
    return removed_employee_time_sheets


async def get_employee_hours_list(employee_id: str, date_start: str, date_end: str, session: Session = None) -> List[EmployeeHours]:
    if session is None:
        session = next(get_db_session())
    try:
        time_sheets = session.query(EmployeeHours).filter(
            EmployeeHours.EmployeeID == employee_id.strip(),
            EmployeeHours.DateWorked.between(date_start.strip(), date_end.strip())
        ).all()
        if time_sheets is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="The employee has no hours logged into the system for the provided range"
                                       " of dates or the employee is not in the database!")
    except IntegrityError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
    return [*time_sheets]


async def get_employee_hours_total(employee_id: str, date_start: str, date_end: str, session: Session = None) -> Dict[str, any]:
    if session is None:
        session = next(get_db_session())
    try:
        total_hours = session.query(
            func.sum(EmployeeHours.WorkHours).label('work_hours'),
            func.sum(EmployeeHours.PTOHours).label('pto_hours'),
            func.sum(EmployeeHours.ExtraHours).label('extra_hours')
        ).filter(
            EmployeeHours.EmployeeID == employee_id.strip(),
            EmployeeHours.DateWorked.between(date_start.strip(), date_end.strip())
        ).one()
        employee_hours_list = await get_employee_hours_list(employee_id.strip(), date_start.strip(), date_end.strip())
        if total_hours is None or None in (total_hours[0], total_hours[1], total_hours[2]) or employee_hours_list is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="The provided employee has no hours logged into the system, "
                                       "or the employee is not in the database!")
        total_hours_and_list = {
            "total_hours": {
                "work_hours": total_hours[0],
                "pto_hours": total_hours[1],
                "extra_hours": total_hours[2],
            },
            "time_sheets": {f"{time_sheet.DateWorked}":time_sheet.as_dict() for time_sheet in employee_hours_list}
        }
    except IntegrityError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
    return total_hours_and_list
