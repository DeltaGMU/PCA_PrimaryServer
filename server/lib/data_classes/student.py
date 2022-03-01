"""
This module contains the MariaDB data classes and Pydantic data classes for the student entity.
The MariaDB data classes are used in database queries and transactions.
The Pydantic data classes are used in requests to the API for ensuring that data received and sent through requests are valid.
For example, creating a new student record through a request to the API will require a Pydantic student data class to define the attributes needed
to create the student entity in the database and validate the data that is sent in the request.
"""

from __future__ import annotations
from typing import Optional
from pydantic import BaseModel
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Date, LargeBinary, VARCHAR, Boolean, Time, sql
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import datetime

Base = declarative_base()


class PydanticStudent(BaseModel):
    """
    A Pydantic class used to represent a student entity when creating a new student record from a http request to the API.
    Do not try to initialize this class as an independent entity or extend it into a subclass.
    """
    first_name: str
    last_name: str


class PydanticStudentCareHoursCheckIn(BaseModel):
    """
    A Pydantic class used to represent a student entity that is being checked into student care when creating a new student care hours record from a http request to the API.
    Do not try to initialize this class as an independent entity or extend it into a subclass.
    The check_in_time for this pydantic class is optional since the server can automatically generate the check-in time if one is not provided.
    """
    student_id: str
    check_in_time: Optional[str]
    check_in_date: str
    care_type: bool


class PydanticStudentCareHoursCheckOut(BaseModel):
    """
    A Pydantic class used to represent a student entity that is being checked out of student care when updating student care hours record from a http request to the API.
    Do not try to initialize this class as an independent entity or extend it into a subclass.
    """
    student_id: str
    check_out_time: str
    check_out_date: str
    care_type: bool


class StudentCareHours(Base):
    """
    A MariaDB data class that represents the table structure of the student care hours table in the database server.
    This is replicated in the server code to ensure that the data being sent to and received from the database are valid.
    Do not attempt to manually modify this class or extend it into a subclass.
    """
    __tablename__ = 'student_care_hours'
    id = Column(Integer, primary_key=True, autoincrement=True, unique=True, nullable=False)
    StudentID = Column(VARCHAR(length=50), ForeignKey('student.id'), nullable=False)
    CareDate = Column(Date, nullable=False, default=sql.func.current_date())
    CheckInTime = Column(Time(timezone=False), nullable=False, default=datetime.datetime.now().strftime('%H:%M:%S'))
    CheckOutTime = Column(Time(timezone=False), nullable=False)
    CareType = Column(Boolean(), nullable=False, default=False)  # CareType: False = Before Care, True = After Care
    EntryCreated = Column(DateTime, nullable=False, default=sql.func.now())

    def __init__(self, student_id: str, care_date: str, care_type: bool, checkin_time: datetime.datetime, checkout_time: datetime.datetime):
        """
        The constructor for the ``StudentCareHours`` data class that is utilized internally by the SQLAlchemy library.
        Only manually instantiate this data class to create employee hours records in the database within database sessions.


        :param student_id: The student id that references the student id key in the student table.
        :type student_id: str, required
        :param care_date: The date that the student care was provided on represented in YYYY-MM-DD format.
        :type care_date: str, required
        :param care_type: The type of care that the student received with False being before-care, and True being after-care.
        :type care_type: bool, required
        :param checkin_time: The time that the student was checked into student care represented as a timestamp.
        :type checkin_time: str, required
        :param checkout_time: The time that the student was checked out of student care represented as a timestamp.
        :type checkout_time: str, required
        """
        self.StudentID = student_id
        self.CareDate = care_date
        self.CareType = care_type
        self.CheckInTime = checkin_time
        self.CheckOutTime = checkout_time

    def as_dict(self):
        """
        A utility method to convert the class attributes into a dictionary format.
        This is useful for representing the entity in a JSON format for a request response.

        :return: Dictionary representation of the data class attributes.
        :rtype: dict
        """
        return {
            "student_id": self.StudentID,
            "check_in_time": self.CheckInTime,
            "check_out_time": self.CheckOutTime,
            "care_date": self.CareDate,
            "care_type": self.CareType,
            "entry_created": self.EntryCreated
        }


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
    StudentEnabled = Column(Boolean(), nullable=False, default=True)
    StudentCareHoursRelationship = relationship('StudentCareHours', cascade='all, delete')
    EntryCreated = Column(DateTime, nullable=False, default=sql.func.now())

    # Do not initialize this except for creating blank student templates!
    def __init__(self, student_id: str, first_name: str, last_name: str, enabled: bool = True):
        """
        The constructor for the ``Student`` data class that is utilized internally by the SQLAlchemy library.
        Only manually instantiate this data class to create employee hours records in the database within database sessions.


        :param student_id: The student id of the student.
        :type student_id: str, required
        :param first_name: The first name of the student.
        :type first_name: str, required
        :param last_name: The last name of the student.
        :type last_name: str, required
        :param enabled: Determines if the individual is active as a student of PCA. Disable this if the student no longer attends PCA or is on indefinite leave.
        :type enabled: bool, optional
        """
        self.StudentID = student_id
        self.FirstName = first_name
        self.LastName = last_name
        self.StudentEnabled = enabled

    def as_dict(self):
        """
        A utility method to convert the class attributes into a dictionary format.
        This is useful for representing the entity in a JSON format for a request response.

        :return: Dictionary representation of the data class attributes.
        :rtype: dict
        """
        return {
            "student_id": self.StudentID,
            "first_name": self.FirstName,
            "last_name": self.LastName,
            "is_enabled": self.StudentEnabled,
            "entry_created": self.EntryCreated
        }
