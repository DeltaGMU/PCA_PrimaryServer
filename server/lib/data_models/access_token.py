"""
This module contains the MariaDB data classes and Pydantic data classes for blacklisting access tokens.
The MariaDB data classes are used in database queries and transactions.
The Pydantic data classes are used in requests to the API for ensuring that data received and sent through requests are valid.
For example, logging out of the web interface will insert the account's access token into the token blacklist.
"""

from sqlalchemy import Column, Integer, VARCHAR, DateTime, sql
from server.lib.database_controllers.sqlalchemy_base_interface import MainEngineBase as Base


class TokenBlacklist(Base):
    """
    A MariaDB data class that represents the table structure of the token_blacklist table in the database server.
    This model is used to generate the token blacklist table in the MariaDB database server.
    """
    __tablename__ = 'token_blacklist'
    id = Column(Integer, primary_key=True, autoincrement=True, unique=True, nullable=False)
    AccessToken = Column(VARCHAR(length=256), unique=True, nullable=False)
    Iss = Column(Integer, nullable=False)
    Exp = Column(Integer, nullable=False)
    EntryCreated = Column(DateTime, nullable=False, default=sql.func.now())

    def __init__(self, token: str, iss: int, exp: int):
        """
        The constructor for the ``TokenBlacklist`` data class that is utilized internally by the SQLAlchemy library.
        Only manually instantiate this data class to create blacklist records for access tokens in the database within database sessions.

        :param token: The access token that should be added to the blacklist table.
        :type token: str, required
        :param iss: The issue time of the access token.
        :type iss: str, required
        :param exp: The expiration time of the access token.
        :type exp: str, required
        """
        self.AccessToken = token
        self.Iss = iss
        self.Exp = exp

    def as_dict(self):
        """
        A utility method to convert the class attributes into a dictionary format.
        This web friendly version hides the internal IDs and other metadata information.

        :return: Web-safe dictionary representation of the data class attributes.
        :rtype: Dict[str, any]
        """
        return {
            "id": self.id,
            "token": self.AccessToken,
            "iss": self.Iss,
            "exp": self.Exp
        }

    def as_detail_dict(self):
        """
        A utility method to convert the class attributes into a dictionary format.
        This is useful for representing the entity in a JSON format for a request response.

        :return: Dictionary representation of the data class attributes.
        :rtype: Dict[str, any]
        """
        return {
            "id": self.id,
            "token": self.AccessToken,
            "iss": self.Iss,
            "exp": self.Exp,
            "entry_created": self.EntryCreated
        }
