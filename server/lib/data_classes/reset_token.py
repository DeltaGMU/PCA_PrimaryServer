from sqlalchemy import Column, Integer, VARCHAR
from server.lib.database_access.sqlalchemy_base import MainEngineBase as Base, main_engine
from pydantic import BaseModel


class PydanticResetToken(BaseModel):
    new_password: str
    reset_token: str


class ResetToken(Base):
    __tablename__ = 'reset_tokens'
    id = Column(Integer, primary_key=True, autoincrement=True, unique=True, nullable=False)
    Token = Column(VARCHAR(length=256), unique=True, nullable=False)
    EmployeeID = Column(VARCHAR(length=256), unique=True, nullable=False)
    Iss = Column(Integer, nullable=False)
    Exp = Column(Integer, nullable=False)

    def __init__(self, token: str, employee_id: str, iss: int, exp: int):
        self.Token = token
        self.EmployeeID = employee_id
        self.Iss = iss
        self.Exp = exp

    def as_dict(self):
        return {
            "id": self.id,
            "token": self.Token,
            "employee_id": self.EmployeeID,
            "iss": self.Iss,
            "exp": self.Exp
        }


Base.metadata.drop_all(bind=main_engine, tables=[ResetToken.__table__])
ResetToken.__table__.create(main_engine)
