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
    FirstName: str
    LastName: str
    StudentEnabled: bool


class PydanticStudentCareHoursCheckIn(BaseModel):
    StudentID: str
    CheckInTime: Optional[str]
    CareDate: str
    CareType: bool


class PydanticStudentCareHoursCheckOut(BaseModel):
    StudentID: str
    CheckOutTime: int
    CareDate: str


class StudentCareHours(Base):
    __tablename__ = 'student_care_hours'
    id = Column(Integer, primary_key=True, autoincrement=True, unique=True, nullable=False)
    StudentID = Column(VARCHAR(length=50), ForeignKey('student.id'), nullable=False)
    CareDate = Column(Date, nullable=False, default=sql.func.current_date())
    CheckInTime = Column(Time(timezone=False), nullable=False, default=datetime.datetime.now().strftime('%H:%M:%S'))
    CheckOutTime = Column(Time(timezone=False), nullable=True)
    CareType = Column(Boolean(), nullable=False, default=False)  # CareType: False = Before Care, True = After Care
    EntryCreated = Column(DateTime, nullable=False, default=sql.func.now())

    # Do not initialize this except for creating blank student_care_hours templates!
    def __init__(self, student_id: str, care_date: str, care_type: bool, checkin_time: datetime.datetime | None = None, checkout_time: datetime.datetime | None = None):
        self.StudentID = student_id
        self.CareDate = care_date
        self.CareType = care_type
        self.CheckInTime = checkin_time
        self.CheckOutTime = checkout_time

    def as_dict(self):
        return {
            "StudentID": self.StudentID,
            "CareDate": self.CareDate,
            "CheckInTime": self.CheckInTime,
            "CheckOutTime": self.CheckOutTime,
            "CareType": self.CareType,
            "EntryCreated": self.EntryCreated
        }


class Student(Base):
    __tablename__ = 'student'
    id = Column(Integer, primary_key=True, autoincrement=True, unique=True, nullable=False)
    StudentID = Column(VARCHAR(length=50), unique=True, nullable=False)
    FirstName = Column(VARCHAR(length=50), nullable=False)
    LastName = Column(VARCHAR(length=50), nullable=False)
    StudentEnabled = Column(Boolean(), nullable=False, default=True)
    StudentCareHoursRelationship = relationship('StudentCareHours', cascade='all, delete')
    EntryCreated = Column(DateTime, nullable=False, default=sql.func.now())

    # Do not initialize this except for creating blank student templates!
    def __init__(self, student_id: str, fname: str, lname: str, enabled: bool):
        self.StudentID = student_id
        self.FirstName = fname
        self.LastName = lname
        self.StudentEnabled = enabled

    def as_dict(self):
        return {
            "StudentID": self.StudentID,
            "FirstName": self.FirstName,
            "LastName": self.LastName,
            "StudentEnabled": self.StudentEnabled,
            "EntryCreated": self.EntryCreated
        }
