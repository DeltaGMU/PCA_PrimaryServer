from __future__ import annotations
from typing import Tuple
from sqlalchemy.orm import Session
from sqlalchemy.sql.functions import func
from server.lib.data_classes.employee_hours import EmployeeHours
from server.lib.database_manager import get_db_session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status


def get_employee_hours(employee_id: str, date_start: str, date_end: str, session: Session = None) -> Tuple[int, int, int]:
    if session is None:
        session = next(get_db_session())
    try:
        total_hours = session.query(
            func.sum(EmployeeHours.WorkHours).label('work_hours'),
            func.sum(EmployeeHours.PTOHours).label('pto_hours'),
            func.sum(EmployeeHours.ExtraHours).label('extra_hours')
        ).filter(
            EmployeeHours.EmployeeID == employee_id,
            EmployeeHours.DateWorked.between(date_start, date_end)
        ).scalar()
        if total_hours is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="The provided employee has no hours logged into the system, "
                                       "or the employee is not in the database!")
    except IntegrityError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
    return total_hours
