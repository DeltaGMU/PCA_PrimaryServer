from pydantic import BaseModel


class PydanticRetrieveEmployeeReport(BaseModel):
    start_date: str
    end_date: str


class PydanticDeleteEmployeeReport(BaseModel):
    date: str