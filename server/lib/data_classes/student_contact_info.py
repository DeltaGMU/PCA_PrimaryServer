"""
This module contains the MariaDB data classes and Pydantic data classes for the student contact information entity.
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
from server.lib.database_access.sqlalchemy_base_interface import MainEngineBase as Base


class PydanticStudentContactInfoRegistration(BaseModel):
    """
    A Pydantic class used to represent a student contact info entity when creating a new contact info record from an HTTP request to the API.
    Do not try to initialize this class as an independent entity or extend it into a subclass.
    """
    student_id: str
    parent_one_first_name: str
    parent_one_last_name: str
    parent_two_first_name: Optional[str]
    parent_two_last_name: Optional[str]
    primary_email: str
    secondary_email: Optional[str]
    enable_notifications: Optional[bool]


class StudentContactInfo(Base):
    """
    A MariaDB data class that represents the table structure of the student contact info table in the database server.
    This is replicated in the server code to ensure that the data being sent to and received from the database are valid.
    This class provides a method of storing contact information for both employees and students.
    Do not attempt to manually modify this class or extend it into a subclass.
    """
    __tablename__ = 'student_contact_info'
    id = Column(Integer, primary_key=True, autoincrement=True, unique=True, nullable=False)
    StudentID = Column(VARCHAR(length=50), ForeignKey('student.StudentID'), nullable=False)
    ParentOneFirstName = Column(VARCHAR(length=100), nullable=False)
    ParentOneLastName = Column(VARCHAR(length=100), nullable=False)
    ParentTwoFirstName = Column(VARCHAR(length=100))
    ParentTwoLastName = Column(VARCHAR(length=100))
    PrimaryEmail = Column(VARCHAR(length=100), nullable=False)
    SecondaryEmail = Column(VARCHAR(length=100), nullable=True)
    EnableNotifications = Column(Boolean(), nullable=False, default=True)
    LastUpdated = Column(DateTime, nullable=False, default=sql.func.now())
    EntryCreated = Column(DateTime, nullable=False, default=sql.func.now())
    StudentParentRelationship = relationship("Student", back_populates="StudentContactInfo")

    # Do not initialize this except for creating blank contact info templates!
    def __init__(self, student_id: str, parent_one_first_name: str, parent_one_last_name: str, primary_email: str,
                 parent_two_first_name: str = None, parent_two_last_name: str = None,
                 secondary_email: str = None, enable_notifications: bool = True):
        """
        The constructor for the ``StudentContactInfo`` data class that is utilized internally by the SQLAlchemy library.
        Only manually instantiate this data class to create contact info records in the database within database sessions.

        :param student_id: The ID of the student to bind the contact information to.
        :type student_id: str, required
        :param primary_email: The primary email address on file for email notifications and alternative login.
        :type primary_email: str, required
        :param secondary_email: The secondary email address on file if email notifications need to be sent to multiple emails.
        :type secondary_email: str, optional
        :param enable_notifications: Enables or disables the use of email notifications for the employee or student that owns the contact information.
        :type enable_notifications: bool, optional
        """
        self.StudentID = student_id
        self.ParentOneFirstName = parent_one_first_name
        self.ParentOneLastName = parent_one_last_name
        self.ParentTwoFirstName = parent_two_first_name
        self.ParentTwoLastName = parent_two_last_name
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
            "parent_one_first_name": self.ParentOneFirstName,
            "parent_one_last_name": self.ParentOneLastName,
            "parent_two_first_name": self.ParentTwoFirstName,
            "parent_two_last_name": self.ParentTwoLastName,
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
            "student_id": self.StudentID,
            "parent_one_first_name": self.ParentOneFirstName,
            "parent_one_last_name": self.ParentOneLastName,
            "parent_two_first_name": self.ParentTwoFirstName,
            "parent_two_last_name": self.ParentTwoLastName,
            "primary_email": self.PrimaryEmail,
            "secondary_email": self.SecondaryEmail,
            "enable_notifications": self.EnableNotifications,
            "last_updated": self.LastUpdated,
            "entry_created": self.EntryCreated
        }
