"""
This module contains the MariaDB data classes and Pydantic data classes for the employee entity.
The MariaDB data classes are used in database queries and transactions.
The Pydantic data classes are used in requests to the API for ensuring that data received and sent through requests are valid.
For example, creating a new employee record through a request to the API will require a Pydantic employee data class to define the attributes needed
to create the employee entity in the database and validate the data that is sent in the request.
"""
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Date, LargeBinary, VARCHAR, Boolean, sql
from server.lib.database_access.sqlalchemy_base import MainEngineBase as Base


class PydanticContactInfoRegistration(BaseModel):
    """
    A Pydantic class used to represent a contact info entity when creating a new contact info record from an HTTP request to the API.
    Do not try to initialize this class as an independent entity or extend it into a subclass.
    """
    owner_id: str
    full_name_of_contact: str
    primary_email: str
    secondary_email: Optional[str]
    enable_notifications: Optional[bool]


class ContactInfo(Base):
    """
    A MariaDB data class that represents the table structure of the contact info table in the database server.
    This is replicated in the server code to ensure that the data being sent to and received from the database are valid.
    This class provides a method of storing contact information for both employees and students.
    Do not attempt to manually modify this class or extend it into a subclass.
    """
    __tablename__ = 'contact_info'
    id = Column(Integer, primary_key=True, autoincrement=True, unique=True, nullable=False)
    OwnerID = Column(VARCHAR(length=50), unique=True, nullable=False)
    FullNameOfContact = Column(VARCHAR(length=100), nullable=False)
    PrimaryEmail = Column(VARCHAR(length=100), nullable=False)
    SecondaryEmail = Column(VARCHAR(length=100), nullable=True)
    EnableNotifications = Column(Boolean(), nullable=False, default=True)
    LastUpdated = Column(DateTime, nullable=False, default=sql.func.now())
    EntryCreated = Column(DateTime, nullable=False, default=sql.func.now())

    # Do not initialize this except for creating blank contact info templates!
    def __init__(self, owner_id: str, full_name_of_contact: str, primary_email: str, secondary_email: str = None, enable_notifications: bool = True):
        """
        The constructor for the ``ContactInfo`` data class that is utilized internally by the SQLAlchemy library.
        Only manually instantiate this data class to create contact info records in the database within database sessions.

        :param full_name_of_contact: The name of the contact that this contact information belongs to. A student's name of contact would be a parent, but an employee's would be themselves.
        :type full_name_of_contact: str, required
        :param primary_email: The primary email address on file for email notifications and alternative login.
        :type primary_email: str, required
        :param secondary_email: The secondary email address on file if email notifications need to be sent to multiple emails.
        :type secondary_email: str, optional
        :param enable_notifications: Enables or disables the use of email notifications for the employee or student that owns the contact information.
        :type enable_notifications: bool, optional
        """
        self.OwnerID = owner_id
        self.FullNameOfContact = full_name_of_contact
        self.PrimaryEmail = primary_email
        self.SecondaryEmail = secondary_email
        self.EnableNotifications = enable_notifications

    def as_dict(self):
        """
        A utility method to convert the class attributes into a dictionary format.
        This web friendly version hides the internal IDs, and other metadata information.

        :return: Dictionary representation of the data class attributes.
        :rtype: Dict[str, any]
        """
        return {
            "full_name_of_contact": self.FullNameOfContact,
            "primary_email": self.PrimaryEmail,
            "secondary_email": self.SecondaryEmail,
            "enable_notifications": self.EnableNotifications,
        }

    def as_detail_dict(self):
        """
        A utility method to convert the class attributes into a dictionary format.
        This is useful for representing the entity in a JSON format for a request response.

        :return: Dictionary representation of the data class attributes.
        :rtype: Dict[str, any]
        """
        return {
            "owner_id": self.OwnerID,
            "full_name_of_contact": self.FullNameOfContact,
            "primary_email": self.PrimaryEmail,
            "secondary_email": self.SecondaryEmail,
            "enable_notifications": self.EnableNotifications,
            "last_updated": self.LastUpdated,
            "entry_created": self.EntryCreated
        }
