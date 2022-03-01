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
    FirstName: str
    LastName: str


class PydanticStudentCareHoursCheckIn(BaseModel):
    """
    A Pydantic class used to represent a student entity that is being checked into student care when creating a new student care hours record from a http request to the API.
    Do not try to initialize this class as an independent entity or extend it into a subclass.
    """
    StudentID: str
    CheckInTime: Optional[str]
    CareDate: str
    CareType: bool


class PydanticStudentCareHoursCheckOut(BaseModel):
    """
    A Pydantic class used to represent a student entity that is being checked out of student care when updating student care hours record from a http request to the API.
    Do not try to initialize this class as an independent entity or extend it into a subclass.
    """
    StudentID: str
    CheckOutTime: str
    CareDate: str
    CareType: bool


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
            "StudentID": self.StudentID,
            "CareDate": self.CareDate,
            "CheckInTime": self.CheckInTime,
            "CheckOutTime": self.CheckOutTime,
            "CareType": self.CareType,
            "EntryCreated": self.EntryCreated
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
    def __init__(self, student_id: str, fname: str, lname: str, enabled: bool = True):
        """
        The constructor for the ``Student`` data class that is utilized internally by the SQLAlchemy library.
        Only manually instantiate this data class to create employee hours records in the database within database sessions.


        :param student_id: The student id of the student.
        :type student_id: str, required
        :param fname: The first name of the student.
        :type fname: str, required
        :param lname: The last name of the student.
        :type lname: str, required
        :param enabled: Determines if the individual is active as a student of PCA. Disable this if the student no longer attends PCA or is on indefinite leave.
        :type enabled: bool, optional
        """
        self.StudentID = student_id
        self.FirstName = fname
        self.LastName = lname
        self.StudentEnabled = enabled

    def as_dict(self):
        """
        A utility method to convert the class attributes into a dictionary format.
        This is useful for representing the entity in a JSON format for a request response.

        :return: Dictionary representation of the data class attributes.
        :rtype: dict
        """
        return {
            "StudentID": self.StudentID,
            "FirstName": self.FirstName,
            "LastName": self.LastName,
            "StudentEnabled": self.StudentEnabled,
            "EntryCreated": self.EntryCreated
        }
