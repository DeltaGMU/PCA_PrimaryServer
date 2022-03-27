"""
This module contains the MariaDB data classes and Pydantic data classes for the student entity.
The MariaDB data classes are used in database queries and transactions.
The Pydantic data classes are used in requests to the API for ensuring that data received and sent through requests are valid.
For example, creating a new student record through a request to the API will require a Pydantic student data class to define the attributes needed
to create the student entity in the database and validate the data that is sent in the request.
"""

from __future__ import annotations
from typing import Optional, Dict, List, Union
from pydantic import BaseModel
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Date, LargeBinary, VARCHAR, Boolean, Time, sql
from sqlalchemy.orm import relationship
from server.lib.database_access.sqlalchemy_base_interface import MainEngineBase as Base


class PydanticStudentRegistration(BaseModel):
    """
    A Pydantic class used to validate student information when creating a new student record from a http request to the API.
    Do not try to initialize this class as an independent entity or extend it into a subclass.
    """
    first_name: str
    last_name: str
    car_pool_number: int
    parent_one_first_name: str
    parent_one_last_name: str
    parent_two_first_name: Optional[str]
    parent_two_last_name: Optional[str]
    primary_email: str
    secondary_email: Optional[str]
    grade: str
    is_enabled: Optional[bool] = True
    enable_primary_email_notifications: Optional[bool] = True
    enable_secondary_email_notifications: Optional[bool] = False


class PydanticStudentUpdate(BaseModel):
    first_name: Optional[str]
    last_name: Optional[str]
    car_pool_number: Optional[int]
    parent_one_first_name: Optional[str]
    parent_one_last_name: Optional[str]
    parent_two_first_name: Optional[str]
    parent_two_last_name: Optional[str]
    primary_email: Optional[str]
    secondary_email: Optional[str]
    grade: Optional[str]
    is_enabled: Optional[bool]
    enable_primary_email_notifications: Optional[bool]
    enable_secondary_email_notifications: Optional[bool]


class PydanticMultipleStudentsUpdate(BaseModel):
    student_updates: Dict[str, PydanticStudentUpdate]


class PydanticStudentsRemoval(BaseModel):
    """
    A Pydantic class used to validate student information when deleting an existing employee record from an HTTP request to the API.
    Do not try to initialize this class as an independent entity or extend it into a subclass.
    """
    student_ids: Union[List[str], str]


class Student(Base):
    """
    A MariaDB data class that represents the table structure of the student table in the database server.
    This is replicated in the server code to ensure that the data being sent to and received from the database are valid.
    Do not attempt to manually modify this class or extend it into a subclass.
    """
    __tablename__ = 'student'
    id = Column(Integer, primary_key=True, autoincrement=True, unique=True, nullable=False)
    StudentID = Column(VARCHAR(length=50), unique=True, nullable=False)
    FirstName = Column(VARCHAR(length=50), nullable=False)
    LastName = Column(VARCHAR(length=50), nullable=False)
    CarpoolNumber = Column(Integer, nullable=False)
    GradeID = Column(Integer, ForeignKey('student_grade.id'), nullable=False)
    StudentGrade = relationship("StudentGrade")
    StudentEnabled = Column(Boolean(), nullable=False, default=True)
    StudentContactInfo = relationship("StudentContactInfo", back_populates="StudentParentRelationship", uselist=False, cascade='all, delete')
    StudentCareHoursRelationship = relationship('StudentCareHours', cascade='all, delete')
    LastUpdated = Column(DateTime, nullable=False, default=sql.func.now())
    EntryCreated = Column(DateTime, nullable=False, default=sql.func.now())

    # Do not initialize this except for creating blank student templates!
    def __init__(self, student_id: str, first_name: str, last_name: str, carpool_number: int, contact_info: StudentContactInfo, grade_id: int, enabled: bool = True):
        """
        The constructor for the ``Student`` data class that is utilized internally by the SQLAlchemy library.
        Only manually instantiate this data class to create employee hours records in the database within database sessions.

        :param student_id: The student id of the student.
        :type student_id: str, required
        :param first_name: The first name of the student.
        :type first_name: str, required
        :param last_name: The last name of the student.
        :type last_name: str, required
        :param carpool_number: The carpool number for student.
        :type carpool_number: int, required
        :param contact_info: The contact info record in the database to relate to.
        :type contact_info: int, required
        :param grade_id: The ID number of the student grade record to be added to the database.
        :type grade_id: int, required
        :param enabled: Determines if the individual is active as a student of PCA. Disable this if the student no longer attends PCA or is on indefinite leave.
        :type enabled: bool, optional
        """
        self.StudentID = student_id
        self.FirstName = first_name
        self.LastName = last_name
        self.CarpoolNumber = carpool_number
        self.StudentContactInfo = contact_info
        self.GradeID = grade_id
        self.StudentEnabled = enabled

    def as_detail_dict(self):
        """
        A utility method to convert the class attributes into a dictionary format.
        This is useful for representing the entity in a JSON format for a request response.

        :return: Dictionary representation of the data class attributes.
        :rtype: Dict[str, any]
        """
        return {
            "student_id": self.StudentID,
            "contact_info": self.StudentContactInfo.as_dict(),
            "grade": self.StudentGrade.as_dict(),
            "grade_id": self.GradeID,
            "carpool_number": self.CarpoolNumber,
            "first_name": self.FirstName,
            "last_name": self.LastName,
            "is_enabled": self.StudentEnabled,
            "last_updated": self.LastUpdated,
            "entry_created": self.EntryCreated
        }

    def as_dict(self):
        """
        A utility method to convert the class attributes into a dictionary format.
        This web friendly version hides the internal IDs, and other metadata information.

        :return: Dictionary representation of the data class attributes.
        :rtype: Dict[str, any]
        """
        return {
            "student_id": self.StudentID,
            "first_name": self.FirstName,
            "last_name": self.LastName,
            "carpool_number": self.CarpoolNumber,
            "contact_info": self.StudentContactInfo.as_dict(),
            "grade": self.StudentGrade.as_dict(),
            "is_enabled": self.StudentEnabled
        }
