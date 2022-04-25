"""
This module contains the MariaDB data classes and Pydantic data classes for the employee entity.
The MariaDB data classes are used in database queries and transactions.
The Pydantic data classes are used in requests to the API for ensuring that data received and sent through requests are valid.
For example, creating a new employee record through a request to the API will require a Pydantic employee data class to define the attributes needed
to create the employee entity in the database and validate the data that is sent in the request.
"""

from typing import Optional, Union, List, Dict
from pydantic import BaseModel
from sqlalchemy import Column, ForeignKey, Integer, DateTime, Date, VARCHAR, Boolean, sql
from sqlalchemy.orm import relationship, backref
from server.lib.database_controllers.sqlalchemy_base_interface import MainEngineBase as Base


class PydanticEmployeeRegistration(BaseModel):
    """
    A Pydantic class used to represent an employee entity when creating a new employee record from an HTTP request to the API.
    Do not try to initialize this class as an independent entity or extend it into a subclass.
    """
    first_name: str
    last_name: str
    primary_email: str
    secondary_email: Optional[str]
    role: str
    pto_hours_enabled: Optional[bool] = True
    extra_hours_enabled: Optional[bool] = True
    is_enabled: Optional[bool] = True
    enable_primary_email_notifications: Optional[bool] = True
    enable_secondary_email_notifications: Optional[bool] = False


class PydanticEmployeeUpdate(BaseModel):
    """
    A Pydantic class used to represent an employee entity when updating an existing employee record from an HTTP request to the API.
    Do not try to initialize this class as an independent entity or extend it into a subclass.
    """
    first_name: Optional[str]
    last_name: Optional[str]
    primary_email: Optional[str]
    secondary_email: Optional[str]
    role: Optional[str]
    pto_hours_enabled: Optional[bool]
    extra_hours_enabled: Optional[bool]
    is_enabled: Optional[bool]
    enable_primary_email_notifications: Optional[bool]
    enable_secondary_email_notifications: Optional[bool]


class PydanticMultipleEmployeesUpdate(BaseModel):
    """
    A Pydantic class containing a list of employee information to update multiple existing employee records from an HTTP request to the API.
    Do not try to initialize this class as an independent entity or extend it into a subclass.
    """
    employee_updates: Dict[str, PydanticEmployeeUpdate]


class PydanticEmployeesRemoval(BaseModel):
    """
    A Pydantic class containing a list of employee IDs that are used to deleting existing employee records from an HTTP request to the API.
    Do not try to initialize this class as an independent entity or extend it into a subclass.
    """
    employee_ids: Union[List[str], str]


class PydanticRetrieveMultipleEmployees(BaseModel):
    """
    A Pydantic class used to retrieve employees from a list of employee IDs from an HTTP request to the API.
    Do not try to initialize this class as an independent entity or extend it into a subclass.
    """
    employee_ids: List[str]


class PydanticUpdatePassword(BaseModel):
    """
    A Pydantic class containing updated password information for a single employee.
    Do not try to initialize this class as an independent entity or extend it into a subclass.
    """
    employee_id: str
    current_password: str
    new_password: str


class PydanticForgotPassword(BaseModel):
    """
    A Pydantic class containing the employee ID of an employee that needs a password reset code sent to their email.
    Do not try to initialize this class as an independent entity or extend it into a subclass.
    """
    employee_id: str


class PydanticResetPassword(BaseModel):
    """
    A Pydantic class containing a new password for an employee identified by a unique reset code.
    Do not try to initialize this class as an independent entity or extend it into a subclass.
    """
    new_password: str
    reset_code: str


class Employee(Base):
    """
    A MariaDB data class that represents the table structure of the employee table in the database server.
    This model is used to generate the employee table in the MariaDB database server.

    :param id: The employee record's primary key.
    :type id: int
    :param EmployeeID: The ID of the employee account.
    :type EmployeeID: str
    :param FirstName: The first name of the employee.
    :type FirstName: str
    :param LastName: The last name of the employee.
    :type LastName: str
    :param PasswordHash: The hashed and salted representation of the employee password.
    :type PasswordHash: str
    :param PTOHoursEnabled: Enable or disable the employee's ability to enter PTO hours in their timesheets.
    :type PTOHoursEnabled: bool
    :param ExtraHoursEnabled: Enable or disable the employee's ability to enter Extra hours in their timesheets.
    :type ExtraHoursEnabled: bool
    :param EmployeeEnabled: Enable or disable the employee account in the system.
    :type EmployeeEnabled: bool
    :param LastUpdated: The timestamp of when the entry was last updated.
    :type LastUpdated: datetime
    :param EntryCreated: The timestamp of when the entry was created.
    :type EntryCreated: datetime
    """
    __tablename__ = 'employee'
    id = Column(Integer, primary_key=True, autoincrement=True, unique=True, nullable=False)
    EmployeeID = Column(VARCHAR(length=50), unique=True, nullable=False)
    FirstName = Column(VARCHAR(length=50), nullable=False)
    LastName = Column(VARCHAR(length=50), nullable=False)
    PasswordHash = Column(VARCHAR(length=60), nullable=False)
    PTOHoursEnabled = Column(Boolean(), nullable=False, default=True)
    ExtraHoursEnabled = Column(Boolean(), nullable=False, default=True)
    EmployeeEnabled = Column(Boolean(), nullable=False, default=True)
    EmployeeRoleID = Column(Integer, ForeignKey('employee_role.id'), nullable=False)
    EmployeeRole = relationship("EmployeeRole", lazy='subquery')
    EmployeeContactInfo = relationship("EmployeeContactInfo", back_populates="EmployeeParentRelationship", uselist=False, cascade='all, delete')
    EmployeeHoursRelationship = relationship('EmployeeHours', cascade='all, delete')
    EmployeeResetToken = relationship('ResetToken', back_populates="EmployeeParentRelationship", uselist=False, cascade='all, delete')
    LastUpdated = Column(DateTime, nullable=False, default=sql.func.now())
    EntryCreated = Column(DateTime, nullable=False, default=sql.func.now())

    def __init__(self, employee_id: str, first_name: str, last_name: str, phash: str, role_id: int,
                 contact_info: EmployeeContactInfo, pto_hours_enabled: bool = True, extra_hours_enabled: bool = True, enabled: bool = True):
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
        :param role_id: The ID number of the employee role record in the database to relate to.
        :type role_id: int, required
        :param contact_info: The employee contact info record to be added to the database.
        :type contact_info: int, required
        :param pto_hours_enabled: Enable or disable the employee's ability to enter PTO hours in their timesheet.
        :type pto_hours_enabled: bool, optional
        :param extra_hours_enabled: Enable or disable the employee's ability to enter Extra hours in their timesheet.
        :type extra_hours_enabled: bool, optional
        :param enabled: Determines if the individual is active as an employee of PCA. Disable this if the employee no longer works at PCA or is on indefinite leave.
        :type enabled: bool, optional
        """
        self.EmployeeID = employee_id
        self.FirstName = first_name
        self.LastName = last_name
        self.PasswordHash = phash
        self.EmployeeRoleID = role_id
        self.EmployeeContactInfo = contact_info
        self.PTOHoursEnabled = pto_hours_enabled
        self.ExtraHoursEnabled = extra_hours_enabled
        self.EmployeeEnabled = enabled

    def as_dict(self):
        """
        A utility method to convert the class attributes into a dictionary format.
        This web friendly version hides the internal IDs, password hash, and other metadata information.

        :return: Web-safe dictionary representation of the data class attributes.
        :rtype: Dict[str, any]
        """
        return {
            "employee_id": self.EmployeeID,
            "first_name": self.FirstName,
            "last_name": self.LastName,
            "contact_info": self.EmployeeContactInfo.as_dict(),
            "role": self.EmployeeRole.as_dict(),
            "pto_hours_enabled": self.PTOHoursEnabled,
            "extra_hours_enabled": self.ExtraHoursEnabled,
            "is_enabled": self.EmployeeEnabled
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
            "role_id": self.EmployeeRoleID,
            "contact_info": self.EmployeeContactInfo.as_dict(),
            "role": self.EmployeeRole.as_dict(),
            "first_name": self.FirstName,
            "last_name": self.LastName,
            "pto_hours_enabled": self.PTOHoursEnabled,
            "extra_hours_enabled": self.ExtraHoursEnabled,
            "is_enabled": self.EmployeeEnabled,
            "last_updated": self.LastUpdated,
            "entry_created": self.EntryCreated
        }
