from pydantic import BaseModel
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Date, LargeBinary, VARCHAR, Boolean, sql
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class PydanticStudent(BaseModel):
    FirstName: str
    LastName: str
    StudentEnabled: bool


class PydanticStudentCareHours(BaseModel):
    StudentID: str
    CareHours: int
    CareDate: str


class StudentCareHours(Base):
    __tablename__ = 'student_care_hours'
    id = Column(Integer, primary_key=True, autoincrement=True, unique=True, nullable=False)
    StudentID = Column(VARCHAR(length=50), ForeignKey('student.id'), nullable=False)
    CareHours = Column(INTEGER(unsigned=True), nullable=False, default=0)
    CareDate = Column(Date, nullable=False)
    EntryCreated = Column(DateTime, nullable=False, default=sql.func.now())

    # Do not initialize this except for creating blank employee_hours templates!
    def __init__(self, student_id: str, care_hours: int, care_date: str):
        self.StudentID = student_id
        self.CareHours = care_hours
        self.CareDate = care_date

    def as_dict(self):
        return {
            "StudentID": self.StudentID,
            "CareHours": self.CareHours,
            "CareDate": self.CareDate,
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
