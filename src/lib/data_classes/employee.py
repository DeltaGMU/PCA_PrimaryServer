from pydantic import BaseModel
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Date, LargeBinary, VARCHAR, Boolean, sql
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class PydanticEmployee(BaseModel):
    RawPassword: str
    FirstName: str
    LastName: str
    EmployeeEnabled: bool


class PydanticEmployeeHours(BaseModel):
    EmployeeID: str
    HoursWorked: int
    DateWorked: str


class EmployeeHours(Base):
    __tablename__ = 'employee_hours'
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    EmployeeID = Column(VARCHAR(length=50), ForeignKey('employees.id'), nullable=False)
    HoursWorked = Column(INTEGER(unsigned=True), nullable=False, default=0)
    DateWorked = Column(Date, nullable=False)
    EntryCreated = Column(DateTime, nullable=False, default=sql.func.now())

    # Do not initialize this except for creating blank employee_hours templates!
    def __init__(self, employee_id: str, hours_worked: int, date_worked: str):
        self.EmployeeID = employee_id
        self.HoursWorked = hours_worked
        self.DateWorked = date_worked

    def as_dict(self):
        return {
            "EmployeeID": self.EmployeeID,
            "HoursWorked": self.HoursWorked,
            "DateWorked": self.DateWorked,
        }


class Employee(Base):
    __tablename__ = 'employees'
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    EmployeeID = Column(VARCHAR(length=50), nullable=False)
    FirstName = Column(VARCHAR(length=50), nullable=False)
    LastName = Column(VARCHAR(length=50), nullable=False)
    PasswordHash = Column(VARCHAR(length=60), nullable=False)
    EmployeeEnabled = Column(Boolean(), nullable=False, default=True)
    EmployeeHoursRelationship = relationship('EmployeeHours', cascade='all, delete')
    EntryCreated = Column(DateTime, nullable=False, default=sql.func.now())

    # Do not initialize this except for creating blank employee templates!
    def __init__(self, employee_id: str, fname: str, lname: str, phash: str, enabled: bool):
        self.EmployeeID = employee_id
        self.FirstName = fname
        self.LastName = lname
        self.PasswordHash = phash
        self.EmployeeEnabled = enabled

    def as_dict(self):
        return {
            "EmployeeID": self.EmployeeID,
            "FirstName": self.FirstName,
            "LastName": self.LastName,
            "PasswordHash": self.PasswordHash,
            "EmployeeEnabled": self.EmployeeEnabled,
            "EntryCreated": self.EntryCreated
        }
