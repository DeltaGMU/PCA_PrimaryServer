"""
This module contains the MariaDB data classes and Pydantic data classes for the employee hours entity (timesheet entity).
The MariaDB data classes are used in database queries and transactions.
The Pydantic data classes are used in requests to the API for ensuring that data received and sent through requests are valid.
For example, creating a new employee hours record through a request to the API will require a Pydantic employee timesheet submission
data class to define the attributes needed to create the timesheet record in the database and validate the data that is sent in the request.
"""
from pydantic.main import BaseModel
from typing import Optional, List, Union
from sqlalchemy.dialects.mysql import INTEGER, FLOAT
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Date, VARCHAR, sql
from server.lib.database_controllers.sqlalchemy_base_interface import MainEngineBase as Base


class PydanticEmployeeTimesheetSubmission(BaseModel):
    """
    A Pydantic class containing the information needed to submit an employee timesheet.
    Do not try to initialize this class as an independent entity or extend it into a subclass.
    """
    work_hours: float
    pto_hours: Optional[float] = 0.0
    extra_hours: Optional[float] = 0.0
    comment: Optional[str] = ""
    date_worked: str


class PydanticEmployeeMultipleTimesheetSubmission(BaseModel):
    """
    A Pydantic class containing a list of employee timesheet submission information to submit multiple time sheets at a time.
    Do not try to initialize this class as an independent entity or extend it into a subclass.
    """
    time_sheets: List[PydanticEmployeeTimesheetSubmission]


class PydanticReadEmployeeTimesheet(BaseModel):
    """
    A Pydantic class containing the information needed to retrieve time sheets from a provided reporting period.
    Do not try to initialize this class as an independent entity or extend it into a subclass.
    """
    date_start: str
    date_end: Optional[str]


class PydanticEmployeeTimesheetUpdate(BaseModel):
    """
    A Pydantic class containing the information needed to update an employee timesheet record.
    Do not try to initialize this class as an independent entity or extend it into a subclass.
    """
    date_worked: str
    work_hours: Optional[float] = 0.0
    pto_hours: Optional[float] = 0.0
    extra_hours: Optional[float] = 0.0
    comment: Optional[str] = ""


class PydanticEmployeeTimesheetRemoval(BaseModel):
    """
    A Pydantic class containing the information needed to delete multiple employee timesheet records by a provided date.
    Do not try to initialize this class as an independent entity or extend it into a subclass.
    """
    dates_worked: Union[List[str], str]


class EmployeeHours(Base):
    """
    A MariaDB data class that represents the table structure of the employee hours table in the database server.
    This model is used to generate the employee_hours table in the MariaDB database server.

    :param id: The employee timesheet record's primary key.
    :type id: int
    :param EmployeeID: The ID of the employee account.
    :type EmployeeID: str
    :param WorkHours: The work hours for the timesheet record.
    :type WorkHours: float
    :param PTOHours: The PTO hours for the timesheet record.
    :type PTOHours: float
    :param ExtraHours: The Extra hours for the timesheet record.
    :type ExtraHours: float
    :param DateWorked: The date that the employee worked.
    :type DateWorked: date
    :param Comment: Optionally, a comment can be added to the timesheet record.
    :type Comment: str, optional
    :param EntryCreated: The timestamp of when the entry was created.
    :type EntryCreated: datetime
    """
    __tablename__ = 'employee_hours'
    id = Column(Integer, primary_key=True, autoincrement=True, unique=True, nullable=False)
    EmployeeID = Column(VARCHAR(length=50), ForeignKey('employee.EmployeeID'), nullable=False)
    WorkHours = Column(FLOAT(precision=3, scale=1, unsigned=True), nullable=False, default=0)
    PTOHours = Column(FLOAT(precision=3, scale=1, unsigned=True), nullable=False, default=0)
    ExtraHours = Column(FLOAT(precision=3, scale=1, unsigned=True), nullable=False, default=0)
    DateWorked = Column(Date, nullable=False)
    Comment = Column(VARCHAR(length=1024), default="")
    EntryCreated = Column(DateTime, nullable=False, default=sql.func.now())

    def __init__(self, employee_id: str, work_hours: float, pto_hours: float, extra_hours: float, date_worked: str, comment: str = ""):
        """
        The constructor for the ``EmployeeHours`` data class that is utilized internally by the SQLAlchemy library.
        Only manually instantiate this data class to create employee hours records in the database within database sessions.

        :param employee_id: The employee id that references the employee id key in the employees table.
        :type employee_id: str, required
        :param work_hours: The hours worked by the employee on the given date in 0.5 hr increments.
        :type work_hours: float, required
        :param pto_hours: The PTO hours by the employee on the given date in 0.5 hr increments. Defaults to 0 if not provided.
        :type pto_hours: float, optional
        :param extra_hours: The extra/overtime hours by the employee on the given date in 0.5 hr increments. Defaults to 0 if not provided.
        :type extra_hours: float, optional
        :param date_worked: The date that the employee hours were worked on represented in YYYY-MM-DD format.
        :type date_worked: str, required
        :param comment: Optional comments made by the employee regarding PTO/extra hours.
        :type comment: str, optional
        """
        self.EmployeeID = employee_id
        self.WorkHours = work_hours
        self.PTOHours = pto_hours
        self.ExtraHours = extra_hours
        self.DateWorked = date_worked
        self.Comment = comment

    def as_dict(self):
        """
        A utility method to convert the class attributes into a dictionary format.
        This web friendly version hides the internal IDs, and other metadata information.

        :return: Dictionary representation of the data class attributes.
        :rtype: Dict[str, any]
        """
        return {
            "work_hours": self.WorkHours,
            "pto_hours": self.PTOHours,
            "extra_hours": self.ExtraHours,
            "date_worked": self.DateWorked,
            "comment": self.Comment
        }

    def as_detail_dict(self):
        """
        A utility method to convert the class attributes into a dictionary format.
        This is useful for representing the entity in a JSON format for a request response.

        :return: Dictionary representation of the data class attributes.
        :rtype: Dict[str, any]
        """
        return {
            "employee_id": self.EmployeeID,
            "work_hours": self.WorkHours,
            "pto_hours": self.PTOHours,
            "extra_hours": self.ExtraHours,
            "date_worked": self.DateWorked,
            "comment": self.Comment,
            "entry_created": self.EntryCreated
        }
