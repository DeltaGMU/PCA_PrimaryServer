"""
This module contains the MariaDB data classes and Pydantic data classes for the employee entity.
The MariaDB data classes are used in database queries and transactions.
The Pydantic data classes are used in requests to the API for ensuring that data received and sent through requests are valid.
For example, creating a new employee record through a request to the API will require a Pydantic employee data class to define the attributes needed
to create the employee entity in the database and validate the data that is sent in the request.
"""

from pydantic import BaseModel
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Date, LargeBinary, VARCHAR, Boolean, sql
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class PydanticEmployee(BaseModel):
    """
    A Pydantic class used to represent an employee entity when creating a new employee record from a http request to the API.
    Do not try to initialize this class as an independent entity or extend it into a subclass.
    """
    plain_password: str
    first_name: str
    last_name: str


class PydanticEmployeeHours(BaseModel):
    """
    A Pydantic class used to represent an employee hours entity when creating a new employee hours record from a http request to the API.
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
    HoursWorked = Column(INTEGER(unsigned=True), nullable=False, default=0)
    DateWorked = Column(Date, nullable=False)
    EntryCreated = Column(DateTime, nullable=False, default=sql.func.now())

    def __init__(self, employee_id: str, hours_worked: int, date_worked: str):
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
        self.HoursWorked = hours_worked
        self.DateWorked = date_worked

    def as_dict(self):
        """
        A utility method to convert the class attributes into a dictionary format.
        This is useful for representing the entity in a JSON format for a request response.

        :return: Dictionary representation of the data class attributes.
        :rtype: dict
        """
        return {
            "employee_id": self.EmployeeID,
            "hours_worked": self.HoursWorked,
            "date_worked": self.DateWorked,
        }


class Employee(Base):
    """
    A MariaDB data class that represents the table structure of the employee table in the database server.
    This is replicated in the server code to ensure that the data being sent to and received from the database are valid.
    Do not attempt to manually modify this class or extend it into a subclass.
    """
    __tablename__ = 'employee'
    id = Column(Integer, primary_key=True, autoincrement=True, unique=True, nullable=False)
    EmployeeID = Column(VARCHAR(length=50), unique=True, nullable=False)
    FirstName = Column(VARCHAR(length=50), nullable=False)
    LastName = Column(VARCHAR(length=50), nullable=False)
    PasswordHash = Column(VARCHAR(length=60), nullable=False)
    EmployeeEnabled = Column(Boolean(), nullable=False, default=True)
    EmployeeHoursRelationship = relationship('EmployeeHours', cascade='all, delete')
    EntryCreated = Column(DateTime, nullable=False, default=sql.func.now())

    # Do not initialize this except for creating blank employee templates!
    def __init__(self, employee_id: str, first_name: str, last_name: str, phash: str, enabled: bool = True):
        """
        The constructor for the ``Employee`` data class that is utilized internally by the SQLAlchemy library.
        Only manually instantiate this data class to create employee records in the database within database sessions.

        :param employee_id: The employee id of the employee.
        :type employee_id: str, required
        :param first_name: The first name of the employee.
        :type first_name: str, required
        :param last_name: The last name of the employee.
        :type last_name: str, required
        :param phash: The hash representation of the employee password generated from the employee utility module.
        :type phash: str, required
        :param enabled: Determines if the individual is active as an employee of PCA. Disable this if the employee no longer works at PCA or is on indefinite leave.
        :type enabled: bool, optional
        """
        self.EmployeeID = employee_id
        self.FirstName = first_name
        self.LastName = last_name
        self.PasswordHash = phash
        self.EmployeeEnabled = enabled

    def as_dict(self):
        """
        A utility method to convert the class attributes into a dictionary format.
        This is useful for representing the entity in a JSON format for a request response.

        :return: Dictionary representation of the data class attributes.
        :rtype: dict
        """
        return {
            "employee_id": self.EmployeeID,
            "first_name": self.FirstName,
            "last_name": self.LastName,
            "password_hash": self.PasswordHash,
            "is_enabled": self.EmployeeEnabled,
            "entry_created": self.EntryCreated
        }
