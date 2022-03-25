from pydantic import BaseModel


class PydanticEmployeeRetrieveReport(BaseModel):
    start_date: str
    end_date: str


class PydanticStudentRetrieveReport(BaseModel):
    start_date: str
    end_date: str
    grade: str


class PydanticDeleteReport(BaseModel):
    date: str
