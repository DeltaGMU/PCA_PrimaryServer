"""
This module contains the Pydantic classes required to create leave requests, employee timesheet reports, and student care service reports.
The Pydantic data classes are used in requests to the API for ensuring that data received and sent through requests are valid.
For example, creating a new employee timesheet report through a request to the API will require a Pydantic employee report
data class to define the attributes needed to create an employee timesheet report for a provided reporting period and validate the data that is sent in the request.
"""
from pydantic import BaseModel
from typing import List, Optional


class PydanticEmployeeRetrieveReport(BaseModel):
    """
    A Pydantic class containing the reporting period information used to generate an employee timesheet report.
    Do not try to initialize this class as an independent entity or extend it into a subclass.
    """
    start_date: str
    end_date: str


class PydanticStudentRetrieveReport(BaseModel):
    """
    A Pydantic class containing the reporting period information used to generate a student care service report.
    Do not try to initialize this class as an independent entity or extend it into a subclass.
    """
    start_date: str
    end_date: str
    grade: str


class PydanticLeaveRequest(BaseModel):
    """
    A Pydantic class containing leave request information used to generate an employee leave request.
    Do not try to initialize this class as an independent entity or extend it into a subclass.
    """
    employee_id: str
    employee_name: str
    current_date: str
    date_of_absence_start: str
    date_of_absence_end: str
    num_full_days: int
    num_half_days: int
    num_hours: int
    absence_reason_list: List[str]
    absence_cover_text: str
    absence_comments: Optional[str]
