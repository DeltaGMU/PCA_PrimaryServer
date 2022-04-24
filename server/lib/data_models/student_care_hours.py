"""
This module contains the MariaDB data classes and Pydantic data classes for the student service care hours entity.
The MariaDB data classes are used in database queries and transactions.
The Pydantic data classes are used in requests to the API for ensuring that data received and sent through requests are valid.
For example, creating a new student care service record through a request to the API will require a Pydantic student care record class
to define the attributes needed to create the student care entity in the database and validate the data that is sent in the request.
"""

from __future__ import annotations
import datetime
from typing import Optional, List
from pydantic import BaseModel
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Date, LargeBinary, VARCHAR, Boolean, Time, sql
from server.lib.database_controllers.sqlalchemy_base_interface import MainEngineBase as Base


class PydanticRetrieveCareStudentsByGrade(BaseModel):
    """
    A Pydantic class used to represent the retrieval of multiple student entities that have been checked into student care.
    Do not try to initialize this class as an independent entity or extend it into a subclass.
    """
    student_grade: str
    care_date: str
    care_type: bool


class PydanticRetrieveStudentCareRecord(BaseModel):
    """
    A Pydantic class used to represent the retrieval of a student care records for a specific student.
    Do not try to initialize this class as an independent entity or extend it into a subclass.
    """
    student_id: str
    start_date: str
    end_date: str


class PydanticRetrieveTotalHoursByGrade(BaseModel):
    """
    A Pydantic class used to represent the retrieval of the total student care hours accumulated by all students in a grade.
    Do not try to initialize this class as an independent entity or extend it into a subclass.
    """
    grade: str
    start_date: str
    end_date: str


class PydanticDeleteStudentCareRecord(BaseModel):
    """
    A Pydantic class used to represent the deletion of a student care record on the given date for the given student ID.
    Do not try to initialize this class as an independent entity or extend it into a subclass.
    """
    student_id: str
    care_date: str
    care_type: Optional[bool]


class PydanticStudentCareHoursCheckIn(BaseModel):
    """
    A Pydantic class used to represent a student entity that is being checked into student care which creates a new student care hours record.
    Do not try to initialize this class as an independent entity or extend it into a subclass.
    The check_in_time for this pydantic class is optional since the server can automatically generate the check-in time if one is not provided.
    """
    student_id: str
    check_in_time: Optional[str]
    check_in_date: str
    check_in_signature: str
    care_type: bool


class PydanticStudentCareHoursCheckOut(BaseModel):
    """
    A Pydantic class used to represent a student entity that is being checked out of student care when updating student care hours record from a http request to the API.
    Do not try to initialize this class as an independent entity or extend it into a subclass.
    """
    student_id: str
    check_out_time: str
    check_out_date: str
    check_out_signature: str
    care_type: bool


class StudentCareHours(Base):
    """
    A MariaDB data class that represents the table structure of the student care hours table in the database server.
    This model is used to generate the student_care_hours table in the MariaDB database server.
    """
    __tablename__ = 'student_care_hours'
    id = Column(Integer, primary_key=True, autoincrement=True, unique=True, nullable=False)
    StudentID = Column(VARCHAR(length=50), ForeignKey('student.StudentID'), nullable=False)
    CareDate = Column(Date, nullable=False, default=sql.func.current_date())
    CheckInTime = Column(Time(timezone=False), nullable=False, default=datetime.datetime.now().strftime('%H:%M:%S'))
    CheckOutTime = Column(Time(timezone=False), nullable=False)
    CareType = Column(Boolean(), nullable=False, default=False)  # CareType: False = Before Care, True = After Care
    CheckInSignature = Column(VARCHAR(length=100), nullable=False)
    CheckOutSignature = Column(VARCHAR(length=100))
    ManuallyCheckedOut = Column(Boolean(), nullable=False, default=False)
    EntryCreated = Column(DateTime, nullable=False, default=sql.func.now())

    def __init__(self, student_id: str, care_date: str, care_type: bool, checkin_time: datetime.datetime, checkout_time: datetime.datetime, checkin_signature: str = None, checkout_signature: str = None):
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
        :type checkin_time: datetime, required
        :param checkout_time: The time that the student was checked out of student care represented as a timestamp.
        :type checkout_time: datetime, required
        :param checkin_signature: The name of the individual that has checked in the student, for record-keeping purposes.
        :type checkin_signature: str, optional
        :param checkout_signature: The name of the individual that has checked out the student, for record-keeping purposes.
        :type checkout_signature: str, optional
        """
        self.StudentID = student_id
        self.CareDate = care_date
        self.CareType = care_type
        self.CheckInTime = checkin_time
        self.CheckOutTime = checkout_time
        self.CheckInSignature = checkin_signature
        self.CheckOutSignature = checkout_signature

    def as_detail_dict(self):
        """
        A utility method to convert the class attributes into a dictionary format.
        This is useful for representing the entity in a JSON format for a request response.

        :return: Dictionary representation of the data class attributes.
        :rtype: Dict[str, any]
        """
        return {
            "student_id": self.StudentID,
            "check_in_time": self.CheckInTime,
            "check_out_time": self.CheckOutTime,
            "care_date": self.CareDate,
            "care_type": self.CareType,
            "check_in_signature": self.CheckInSignature,
            "check_out_signature": self.CheckOutSignature,
            "manually_checked_out": self.ManuallyCheckedOut,
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
            "check_in_time": self.CheckInTime,
            "check_out_time": self.CheckOutTime,
            "care_date": self.CareDate,
            "care_type": self.CareType,
            "check_in_signature": self.CheckInSignature,
            "check_out_signature": self.CheckOutSignature,
            "manually_checked_out": self.ManuallyCheckedOut
        }
