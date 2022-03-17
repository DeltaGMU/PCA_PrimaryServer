from sqlalchemy import Column, Integer, VARCHAR
from server.lib.database_access.sqlalchemy_base import MainEngineBase as Base, main_engine
from pydantic import BaseModel


class PydanticResetToken(BaseModel):
    new_password: str
    reset_token: str


class ResetToken(Base):
    __tablename__ = 'reset_tokens'
    id = Column(Integer, primary_key=True, autoincrement=True, unique=True, nullable=False)
    token = Column(VARCHAR(length=256), unique=True, nullable=False)
    employee_id = foreign key
    iss = Column(Integer, nullable=False)
    exp = Column(Integer, nullable=False)

    def __init__(self, token: str, iss: int, exp: int):
        self.token = token
        self.iss = iss
        self.exp = exp

    def as_dict(self):
        return {
            "id": self.id,
            "token": self.token,
            "iss": self.iss,
            "exp": self.exp
        }


Base.metadata.drop_all(bind=main_engine, tables=[ResetToken.__table__])
ResetToken.__table__.create(main_engine)
