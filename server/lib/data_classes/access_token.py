from sqlalchemy import Column, Integer, VARCHAR
from server.lib.database_access.sqlalchemy_base_interface import MainEngineBase as Base


class TokenBlacklist(Base):
    __tablename__ = 'token_blacklist'
    id = Column(Integer, primary_key=True, autoincrement=True, unique=True, nullable=False)
    AccessToken = Column(VARCHAR(length=256), unique=True, nullable=False)
    Iss = Column(Integer, nullable=False)
    Exp = Column(Integer, nullable=False)

    def __init__(self, token: str, iss: int, exp: int):
        self.AccessToken = token
        self.Iss = iss
        self.Exp = exp

    def as_dict(self):
        return {
            "id": self.id,
            "token": self.AccessToken,
            "iss": self.Iss,
            "exp": self.Exp
        }
