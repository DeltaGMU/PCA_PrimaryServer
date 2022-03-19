from sqlalchemy import Column, Integer, VARCHAR
from server.lib.database_access.sqlalchemy_base_interface import MainEngineBase as Base, main_engine


class TokenBlacklist(Base):
    __tablename__ = 'token_blacklist'
    id = Column(Integer, primary_key=True, autoincrement=True, unique=True, nullable=False)
    Token = Column(VARCHAR(length=256), unique=True, nullable=False)
    Iss = Column(Integer, nullable=False)
    Exp = Column(Integer, nullable=False)

    def __init__(self, token: str, iss: int, exp: int):
        self.Token = token
        self.Iss = iss
        self.Exp = exp

    def as_dict(self):
        return {
            "id": self.id,
            "token": self.Token,
            "iss": self.Iss,
            "exp": self.Exp
        }
