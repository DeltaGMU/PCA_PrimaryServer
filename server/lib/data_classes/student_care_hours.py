from __future__ import annotations
import datetime
from typing import Optional
from pydantic import BaseModel
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Date, LargeBinary, VARCHAR, Boolean, Time, sql
from server.lib.database_functions.sqlalchemy_base import MainEngineBase as Base


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
        :rtype: Dict[str, any]
        """
        return {
            "student_id": self.StudentID,
            "check_in_time": self.CheckInTime,
            "check_out_time": self.CheckOutTime,
            "care_date": self.CareDate,
            "care_type": self.CareType,
            "entry_created": self.EntryCreated
        }
