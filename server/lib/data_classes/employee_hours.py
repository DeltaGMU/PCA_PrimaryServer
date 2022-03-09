from pydantic.main import BaseModel
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Date, VARCHAR, sql
from server.lib.database_functions.sqlalchemy_base import MainEngineBase as Base


class PydanticEmployeeHours(BaseModel):
    """
    A Pydantic class used to represent an employee hours entity when creating a new employee hours record from an HTTP request to the API.
    Do not try to initialize this class as an independent entity or extend it into a subclass.
    """
    employee_id: str
    hours_worked: int
    date_worked: str


class EmployeeHours(Base):
    """
    A MariaDB data class that represents the table structure of the employee hours table in the database server.
    This is replicated in the server code to ensure that the data being sent to and received from the database are valid.
    Do not attempt to manually modify this class or extend it into a subclass.
    """
    __tablename__ = 'employee_hours'
    id = Column(Integer, primary_key=True, autoincrement=True, unique=True, nullable=False)
    EmployeeID = Column(VARCHAR(length=50), ForeignKey('employee.id'), nullable=False)
    WorkHours = Column(INTEGER(unsigned=True), nullable=False, default=0)
    PTOHours = Column(INTEGER(unsigned=True), nullable=False, default=0)
    ExtraHours = Column(INTEGER(unsigned=True), nullable=False, default=0)
    DateWorked = Column(Date, nullable=False)
    EntryCreated = Column(DateTime, nullable=False, default=sql.func.now())

    def __init__(self, employee_id: str, work_hours: int, pto_hours: int, extra_hours: int, date_worked: str):
        """
        The constructor for the ``EmployeeHours`` data class that is utilized internally by the SQLAlchemy library.
        Only manually instantiate this data class to create employee hours records in the database within database sessions.

        :param employee_id: The employee id that references the employee id key in the employees table.
        :type employee_id: str, required
        :param hours_worked: The hours worked by the employee on the given date.
        :type hours_worked: int, required
        :param date_worked: The date that the employee hours were worked on represented in YYYY-MM-DD format.
        :type date_worked: str, required
        """
        self.EmployeeID = employee_id
        self.WorkHours = work_hours
        self.PTOHours = pto_hours
        self.ExtraHours = extra_hours
        self.DateWorked = date_worked

    def as_dict(self):
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
        }
