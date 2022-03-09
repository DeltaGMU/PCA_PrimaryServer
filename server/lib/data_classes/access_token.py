from sqlalchemy import Column, Integer, VARCHAR
from server.lib.database_functions.sqlalchemy_base import MemoryEngineBase as Base


class TokenBlacklist(Base):
    __tablename__ = 'token_blacklist'
    id = Column(Integer, primary_key=True, autoincrement=True, unique=True, nullable=False)
    token = Column(VARCHAR(length=256), unique=True, nullable=False)
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