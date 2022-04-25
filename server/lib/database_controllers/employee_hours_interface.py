"""
This module contains the functions that interface with the database server
to handle the processing of employee time sheets. Any code related to the handling of
employing time sheets that require creating, reading, updating, or deleting data from the database server
must use this interface module.
"""

from __future__ import annotations
from typing import Dict, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from lib.strings import LOG_ERROR_GENERAL, LOG_ORIGIN_API
from server.lib.logging_manager import LoggingManager
from server.lib.utils.timesheet_utils import round_hours_to_custom_increment
from server.lib.utils.email_utils import send_email
from server.lib.data_models.employee import Employee
from server.lib.utils.date_utils import check_date_formats
from server.lib.data_models.employee_hours import EmployeeHours, PydanticEmployeeTimesheetSubmission, PydanticEmployeeTimesheetRemoval
from server.lib.database_manager import get_db_session


async def create_employee_multiple_hours(employee_id: str, employee_updates: List[PydanticEmployeeTimesheetSubmission], session: Session = None) -> List[EmployeeHours]:
    """
    This method inserts or updates the timesheet records for an employee and returns
    a list of the employee records that have had their timesheet records updated.
    If timesheet information is submitted for an employee that does not have an existing record, it will be inserted.
    If timesheet information is submitted for an employee with an existing record, it will instead update the existing record.
    Upon successful insertion or updating of the employee timesheet records an email is sent to the employee notifying them
    of the timesheet submission.

    :param employee_id: The ID of the employee.
    :type employee_id: str, required
    :param employee_updates: The list of timesheet submissions for the employee.
    :type employee_updates: List[PydanticEmployeeTimesheetSubmission]
    :param session: The database session.
    :type session: Session
    :return: A list of the employee timesheet records that have been created or updated.
    :rtype: List[Employees]
    :raises HTTPException: If one or more provided parameters are invalid, or the requested data is not found in the database.
    """
    if session is None:
        session = next(get_db_session())
    if None in (employee_id, *employee_updates):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="One or more provided parameters are invalid! Please check the submitted data.")
    try:
        if not check_date_formats([employee_update.date_worked for employee_update in employee_updates]):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="One or more provided dates are not in the YYYY-MM-DD format!")

        employee_id = employee_id.lower().strip()
        check_employee = session.query(Employee).filter(
            Employee.EmployeeID == employee_id
        ).first()
        if check_employee is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not find an employee with the provided employee ID!")

        submitted_time_sheets = []
        for timesheet in employee_updates:
            if not check_employee.PTOHoursEnabled:
                timesheet.pto_hours = 0
            if not check_employee.ExtraHoursEnabled:
                timesheet.extra_hours = 0
            # Round all the timesheet hours to the nearest 0.5 hr increment.
            timesheet.work_hours = round_hours_to_custom_increment(timesheet.work_hours)
            timesheet.extra_hours = round_hours_to_custom_increment(timesheet.extra_hours)
            timesheet.pto_hours = round_hours_to_custom_increment(timesheet.pto_hours)
            timesheet_submission = EmployeeHours(
                employee_id,
                timesheet.work_hours,
                timesheet.pto_hours,
                timesheet.extra_hours,
                timesheet.date_worked,
                timesheet.comment
            )
            timesheet_exists = session.query(EmployeeHours).filter(
                EmployeeHours.EmployeeID == employee_id,
                EmployeeHours.DateWorked == timesheet.date_worked
            ).first()
            if timesheet_exists:
                # Duplicate key detected, so just update the record instead.
                session.query(EmployeeHours).filter(
                    EmployeeHours.EmployeeID == employee_id,
                    EmployeeHours.DateWorked == timesheet.date_worked
                ).update({
                    EmployeeHours.WorkHours: timesheet.work_hours,
                    EmployeeHours.PTOHours: timesheet.pto_hours,
                    EmployeeHours.ExtraHours: timesheet.extra_hours,
                    EmployeeHours.Comment: timesheet.comment
                })
                submitted_time_sheets.append(timesheet_exists)
            else:
                # Skip timesheet entry if the work hours, pto hours, and the extra hours are all 0.
                if timesheet.work_hours == 0 and timesheet.pto_hours == 0 and timesheet.extra_hours == 0:
                    continue
                session.add(timesheet_submission)
                submitted_time_sheets.append(timesheet_submission)
        session.commit()
        if len(submitted_time_sheets) > 0:
            LoggingManager().log(LoggingManager.LogLevel.LOG_INFO,
                                 f"One or more employee time sheets have been inserted/updated in the database for {employee_id}.",
                                 origin=LOG_ORIGIN_API, no_print=False)
            # Send notification to enabled emails that the timesheet has been updated.
            send_emails_to = [check_employee.EmployeeContactInfo.PrimaryEmail]
            if check_employee.EmployeeContactInfo.EnableSecondaryEmailNotifications:
                send_emails_to.append(check_employee.EmployeeContactInfo.SecondaryEmail)
            if len(send_emails_to) > 0:
                send_email(
                    to_user=f'{check_employee.FirstName} {check_employee.LastName}',
                    to_email=send_emails_to,
                    subj="Employee Timesheet Saved",
                    messages=["Your employee timesheet was updated and saved!",
                              "If you are not aware of updates to your employee timesheet, please contact administration staff!"]
                )
    except IntegrityError as err:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
    return submitted_time_sheets


async def create_employee_hours(employee_id: str, date_worked: str, work_hours: float, pto_hours: float = 0, extra_hours: float = 0, comment: str = "", session: Session = None) -> EmployeeHours:
    """
    This method inserts a single timesheet record for an employee and returns the inserted employee record.
    This method does not update the timesheet record if it already exists, instead a duplicate entry error is thrown.

    :param employee_id: The ID of the employee.
    :type employee_id: str, required
    :param date_worked: The date of work for the employee timesheet record.
    :type date_worked: str, required
    :param work_hours: The number of hours worked by the employee on the provided date.
    :type work_hours: float, required
    :param pto_hours: The number of PTO hours taken by the employee on the provided date.
    :type pto_hours: float, optional
    :param extra_hours: The number of extra hours worked by the employee on the provided date.
    :type extra_hours: float, optional
    :param comment: A comment created by the employee for the timesheet submission.
    :type comment: str, optional
    :param session: The database session used to insert the employee timesheet record.
    :type session: Session, optional
    :return: The employee timesheet record that was inserted into the database.
    :rtype: EmployeeHours
    :raises HTTPException: If any provided parameters are invalid, or a duplicate data entry was attempted.
    """
    if session is None:
        session = next(get_db_session())
    if None in (employee_id, date_worked, work_hours, pto_hours, extra_hours):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="One or more provided parameters are invalid! Please check the submitted data.")
    try:
        if not check_date_formats(date_worked):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="One or more provided dates are not in the YYYY-MM-DD format!")
        # Round all the timesheet hours to the nearest 0.5 hr increment.
        work_hours = round_hours_to_custom_increment(work_hours)
        extra_hours = round_hours_to_custom_increment(extra_hours)
        pto_hours = round_hours_to_custom_increment(pto_hours)
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
                date_worked,
                comment
            )
            session.add(timesheet_submission)
            session.commit()
            LoggingManager().log(LoggingManager.LogLevel.LOG_INFO,
                                 f"One or more employee time sheets have been inserted into the database for {employee_id}.",
                                 origin=LOG_ORIGIN_API, no_print=False)
        else:
            session.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Duplicate date entry! The employee already has hours entered for this day! You can update this entry instead using an UPDATE request.")
    except IntegrityError as err:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
    return timesheet_submission


async def update_employee_hours(employee_id: str, date_worked: str, work_hours: float = 0, pto_hours: float = 0, extra_hours: float = 0, comment: str = "", session: Session = None) -> EmployeeHours:
    """
    This method updates a single timesheet record for an employee and returns the updated employee record.
    This method does not insert a timesheet record if it doesn't exist, instead an error is thrown if the record doesn't exist.

    :param employee_id: The ID of the employee.
    :type employee_id: str, required
    :param date_worked: The date of work for the employee timesheet record.
    :type date_worked: str, required
    :param work_hours: The number of hours worked by the employee on the provided date.
    :type work_hours: float, optional
    :param pto_hours: The number of PTO hours taken by the employee on the provided date.
    :type pto_hours: float, optional
    :param extra_hours: The number of extra hours worked by the employee on the provided date.
    :type extra_hours: float, optional
    :param comment: A comment created by the employee for the timesheet submission.
    :type comment: str, optional
    :param session: The database session used to insert the employee timesheet record.
    :type session: Session, optional
    :return: The employee timesheet record that was inserted into the database.
    :rtype: EmployeeHours
    :raises HTTPException: If any provided parameters are invalid, or the timesheet record does not exist.
    """
    if session is None:
        session = next(get_db_session())
    try:
        # Round all the timesheet hours to the nearest 0.5 hr increment.
        work_hours = round_hours_to_custom_increment(work_hours)
        extra_hours = round_hours_to_custom_increment(extra_hours)
        pto_hours = round_hours_to_custom_increment(pto_hours)
        session.query(
            EmployeeHours
        ).filter(
            EmployeeHours.EmployeeID == employee_id,
            EmployeeHours.DateWorked == date_worked
        ).update(
            {
                EmployeeHours.WorkHours: work_hours,
                EmployeeHours.PTOHours: pto_hours,
                EmployeeHours.ExtraHours: extra_hours,
                EmployeeHours.Comment: comment
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
        LoggingManager().log(LoggingManager.LogLevel.LOG_INFO,
                             f"One or more employee time sheets have been updated in the database for {employee_id}.",
                             origin=LOG_ORIGIN_API, no_print=False)
    except IntegrityError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
    return updated_hours


async def delete_all_employee_time_sheets(employee_id: str, session: Session = None):
    """
    This method deletes all the timesheet records for a single employee from the provided employee ID.

    :param employee_id: The ID of the employee.
    :type employee_id: str, required
    :param session: The database session used to delete all the employee's timesheet records.
    :type session: Session, optional
    """
    session.query(EmployeeHours).filter(
        EmployeeHours.EmployeeID == employee_id.lower().strip()
    ).delete()
    session.commit()
    LoggingManager().log(LoggingManager.LogLevel.LOG_INFO,
                         f"All employee time sheets have been deleted in the database for {employee_id}.",
                         origin=LOG_ORIGIN_API, no_print=False)


async def delete_employee_time_sheets(employee_id: str, dates_worked: PydanticEmployeeTimesheetRemoval, session: Session = None) -> List[EmployeeHours]:
    """
    This method deletes the timesheet records of an employee for the specified dates worked.

    :param employee_id: The ID of the employee.
    :type employee_id: str, required
    :param dates_worked: A list of the dates worked, or a single date worked, by the employee that need to have their records deleted.
    :type dates_worked: PydanticEmployeeTimesheetRemoval, required
    :param session: The database session used to delete employee timesheet records.
    :type session: Session, optional
    :return: A list of all the employee timesheet records that were deleted from the database.
    :rtype: List[EmployeeHours]
    :raises HTTPException: If any provided parameters are invalid, or the timesheet records for the provided date do not exist.
    """
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
            LoggingManager().log(LoggingManager.LogLevel.LOG_INFO,
                                 f"One or more employee time sheets have been deleted for {employee_id}.",
                                 origin=LOG_ORIGIN_API, no_print=False)
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
            LoggingManager().log(LoggingManager.LogLevel.LOG_INFO,
                                 f"An employee time sheet on {dates_worked.strip()} has been deleted in the database for {employee_id}.",
                                 origin=LOG_ORIGIN_API, no_print=False)
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot remove an employee time sheet that does not exist in the database!")
    return removed_employee_time_sheets


async def get_employee_hours_list(employee_id: str, date_start: str, date_end: str, session: Session = None) -> List[EmployeeHours]:
    """
    This method retrieves all the employee timesheet records for an employee from the provided range of work dates.

    :param employee_id: The ID of the employee.
    :type employee_id: str, required
    :param date_start: The start work date for the range of employee timesheet records to retrieve.
    :type date_start: str, required
    :param date_end: The end work date for the range of employee timesheet records to retrieve.
    :type date_end: str, required
    :param session: The database session used to retrieve employee timesheet records.
    :type session: Session, optional
    :return: A list of all the employee timesheet records for the provided range of work dates.
    :rtype: List[EmployeeHours]
    :raises HTTPException: If an error is encountered retrieving employee timesheet records from the database.
    """
    if session is None:
        session = next(get_db_session())
    try:
        time_sheets = session.query(EmployeeHours).filter(
            EmployeeHours.EmployeeID == employee_id.strip(),
            EmployeeHours.DateWorked.between(date_start.strip(), date_end.strip())
        ).all()
    except IntegrityError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
    return [*time_sheets]


async def get_employee_hours_total(employee_id: str, date_start: str, date_end: str, session: Session = None, hours_only: bool = False) -> Dict[str, any]:
    """
    This method retrieves the total number of work hours, pto hours, and extra hours for an employee accumulated over
    the provided range of work dates. If an employee has no timesheet submissions for the provided range of work dates,
    then the work hours, pto hours, and extra hours will be 0.

    :param employee_id: The ID of the employee.
    :type employee_id: str, required
    :param date_start: The start work date for the range of employee timesheet records to retrieve.
    :type date_start: str, required
    :param date_end: The end work date for the range of employee timesheet records to retrieve.
    :type date_end: str, required
    :param session: The database session used to retrieve employee timesheet records and total accumulated hours.
    :type session: Session, optional
    :param hours_only: If true, will only provide the total hours accumulated instead of also providing the list of individual timesheet records over the provided range of work dates.
    :type hours_only: bool, optional
    :return: A JSON-Compatible dictionary of the total work hours, pto hours, and extra hours accumulated by the employee timesheet records over the provided range of work dates.
    :rtype: Dict[str, any]
    :raises HTTPException: If an error is encountered retrieving employee timesheet records from the database.
    """
    if session is None:
        session = next(get_db_session())
    try:
        employee_hours_list = await get_employee_hours_list(employee_id.strip(), date_start.strip(), date_end.strip(), session)
        if employee_hours_list is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="The provided employee has no hours logged into the system, "
                                       "or the employee is not in the database!")
        total_hours = {
            "work_hours": 0,
            "pto_hours": 0,
            "extra_hours": 0,
        }
        for record in employee_hours_list:
            total_hours['work_hours'] += record.WorkHours
            total_hours['pto_hours'] += record.PTOHours
            total_hours['extra_hours'] += record.ExtraHours
        total_hours_and_list = {
            "total_hours": total_hours
        }
        # If hours_only is disabled, then also include a list of the individual timesheet records over the range of work dates.
        if not hours_only:
            total_hours_and_list.update({"time_sheets": {f"{time_sheet.DateWorked}": time_sheet.as_dict() for time_sheet in employee_hours_list}})
    except IntegrityError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
    return total_hours_and_list
