"""
This module contains the MariaDB data classes and Pydantic data classes for the employee contact information entity.
The MariaDB data classes are used in database queries and transactions.
The Pydantic data classes are used in requests to the API for ensuring that data received and sent through requests are valid.
For example, creating a new employee record through a request to the API will require a Pydantic employee data class to define the attributes needed
to create the employee entity in the database and validate the data that is sent in the request.
"""
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Date, LargeBinary, VARCHAR, Boolean, sql
from sqlalchemy.orm import relationship
from server.lib.database_controllers.sqlalchemy_base_interface import MainEngineBase as Base


class PydanticEmployeeContactInfoRegistration(BaseModel):
    """
    A Pydantic class used to represent a student contact info entity when creating a new contact info record from an HTTP request to the API.
    Do not try to initialize this class as an independent entity or extend it into a subclass.
    """
    employee_id: str
    full_name_of_contact: str
    primary_email: str
    secondary_email: Optional[str]
    enable_primary_email_notifications: Optional[bool]
    enable_secondary_email_notifications: Optional[bool]


class EmployeeContactInfo(Base):
    """
    A MariaDB data class that represents the table structure of the employee contact info table in the database server.
    This is replicated in the server code to ensure that the data being sent to and received from the database are valid.
    This class provides a method of storing contact information for both employees and students.
    Do not attempt to manually modify this class or extend it into a subclass.
    """
    __tablename__ = 'employee_contact_info'
    id = Column(Integer, primary_key=True, autoincrement=True, unique=True, nullable=False)
    EmployeeID = Column(VARCHAR(length=50), ForeignKey('employee.EmployeeID'), nullable=False)
    PrimaryEmail = Column(VARCHAR(length=100), nullable=False)
    SecondaryEmail = Column(VARCHAR(length=100), nullable=True)
    EnablePrimaryEmailNotifications = Column(Boolean(), nullable=False, default=True)
    EnableSecondaryEmailNotifications = Column(Boolean(), nullable=False, default=False)
    LastUpdated = Column(DateTime, nullable=False, default=sql.func.now())
    EntryCreated = Column(DateTime, nullable=False, default=sql.func.now())
    EmployeeParentRelationship = relationship("Employee", back_populates="EmployeeContactInfo")

    # Do not initialize this except for creating blank contact info templates!
    def __init__(self, employee_id: str, primary_email: str, secondary_email: str = None,
                 enable_primary_email_notifications: bool = True, enable_secondary_email_notifications: bool = False):
        """
        The constructor for the ``EmployeeContactInfo`` data class that is utilized internally by the SQLAlchemy library.
        Only manually instantiate this data class to create contact info records in the database within database sessions.

        :param employee_id: The ID of the employee to bind the contact information to.
        :type employee_id: str, required
        :param primary_email: The primary email address on file for email notifications and alternative login.
        :type primary_email: str, required
        :param secondary_email: The secondary email address on file if email notifications need to be sent to multiple emails.
        :type secondary_email: str, optional
        :param enable_primary_email_notifications: Enables or disables the use of email notifications to the primary email provided.
        :type enable_primary_email_notifications: bool, optional
        :param enable_secondary_email_notifications: Enables or disables the use of email notifications to the secondary email provided.
        :type enable_secondary_email_notifications: bool, optional
        """
        self.EmployeeID = employee_id
        self.PrimaryEmail = primary_email
        self.SecondaryEmail = secondary_email
        self.EnablePrimaryEmailNotifications = enable_primary_email_notifications
        self.EnableSecondaryEmailNotifications = enable_secondary_email_notifications

    def as_dict(self):
        """
        A utility method to convert the class attributes into a dictionary format.
        This web friendly version hides the internal IDs, and other metadata information.

        :return: Dictionary representation of the data class attributes.
        :rtype: Dict[str, any]
        """
        return {
            "primary_email": self.PrimaryEmail,
            "secondary_email": self.SecondaryEmail,
            "enable_primary_email_notifications": self.EnablePrimaryEmailNotifications,
            "enable_secondary_email_notifications": self.EnableSecondaryEmailNotifications,
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
            "primary_email": self.PrimaryEmail,
            "secondary_email": self.SecondaryEmail,
            "enable_primary_email_notifications": self.EnablePrimaryEmailNotifications,
            "enable_secondary_email_notifications": self.EnableSecondaryEmailNotifications,
            "last_updated": self.LastUpdated,
            "entry_created": self.EntryCreated
        }
