from sqlalchemy import Column, Integer, VARCHAR, DateTime, sql
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.orm import relationship
from pydantic import BaseModel
from server.lib.database_controllers.sqlalchemy_base_interface import MainEngineBase as Base


class PydanticResetToken(BaseModel):
    new_password: str
    reset_token: str


class ResetToken(Base):
    __tablename__ = 'reset_tokens'
    id = Column(Integer, primary_key=True, autoincrement=True, unique=True, nullable=False)
    EmployeeID = Column(VARCHAR(length=50), ForeignKey('employee.EmployeeID'), unique=True, nullable=False)
    ResetToken = Column(VARCHAR(length=8), nullable=False)
    Iss = Column(Integer, nullable=False)
    Exp = Column(Integer, nullable=False)
    EntryCreated = Column(DateTime, nullable=False, default=sql.func.now())
    EmployeeParentRelationship = relationship("Employee", back_populates="EmployeeResetToken")

    def __init__(self, token: str, employee_id: str, iss: int, exp: int):
        self.ResetToken = token
        self.EmployeeID = employee_id
        self.Iss = iss
        self.Exp = exp

    def as_detail_dict(self):
        return {
            "id": self.id,
            "token": self.ResetToken,
            "employee_id": self.EmployeeID,
            "iss": self.Iss,
            "exp": self.Exp,
            "entry_created": self.EntryCreated
        }

    def as_dict(self):
        return {
            "token": self.ResetToken,
            "employee_id": self.EmployeeID,
            "iss": self.Iss,
            "exp": self.Exp
        }
