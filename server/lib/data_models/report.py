from pydantic import BaseModel
from typing import List, Optional


class PydanticEmployeeRetrieveReport(BaseModel):
    start_date: str
    end_date: str


class PydanticStudentRetrieveReport(BaseModel):
    start_date: str
    end_date: str
    grade: str


class PydanticLeaveRequest(BaseModel):
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
