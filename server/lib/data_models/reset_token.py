"""
This module contains the MariaDB data classes and Pydantic data classes for employee account password reset tokens.
The MariaDB data classes are used in database queries and transactions.
The Pydantic data classes are used in requests to the API for ensuring that data received and sent through requests are valid.
For example, when an employee requests a password reset for their account, a temporary reset token is generated and stored in the database.
"""

from sqlalchemy import Column, Integer, VARCHAR, DateTime, sql
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.orm import relationship
from pydantic import BaseModel
from server.lib.database_controllers.sqlalchemy_base_interface import MainEngineBase as Base


class PydanticResetToken(BaseModel):
    """
    A Pydantic class containing the new employee account's password and the associated reset token.
    Do not try to initialize this class as an independent entity or extend it into a subclass.
    """
    new_password: str
    reset_token: str


class ResetToken(Base):
    """
    A MariaDB data class that represents the table structure of the reset tokens table in the database server.
    This model is used to generate the reset_tokens table in the MariaDB database server.
    """
    __tablename__ = 'reset_tokens'
    id = Column(Integer, primary_key=True, autoincrement=True, unique=True, nullable=False)
    EmployeeID = Column(VARCHAR(length=50), ForeignKey('employee.EmployeeID'), unique=True, nullable=False)
    ResetToken = Column(VARCHAR(length=8), nullable=False)
    Iss = Column(Integer, nullable=False)
    Exp = Column(Integer, nullable=False)
    EntryCreated = Column(DateTime, nullable=False, default=sql.func.now())
    EmployeeParentRelationship = relationship("Employee", back_populates="EmployeeResetToken")

    def __init__(self, token: str, employee_id: str, iss: int, exp: int):
        """
        The constructor for the ``ResetToken`` data class that is utilized internally by the SQLAlchemy library.
        Only manually instantiate this data class to create new employee password reset token records in the database within database sessions.

        :param token: The temporary reset token associated with an employee account.
        :type token: str, required
        :param employee_id: The ID of the employee account that requested a password reset.
        :type employee_id: str, required
        :param iss: The issue time of the reset token.
        :type iss: int, required
        :param exp: The expiration time of the reset token.
        :type exp: int, required
        """
        self.ResetToken = token
        self.EmployeeID = employee_id
        self.Iss = iss
        self.Exp = exp

    def as_detail_dict(self):
        """
        A utility method to convert the class attributes into a dictionary format.
        This is useful for representing the entity in a JSON format for a request response.

        :return: Dictionary representation of the data class attributes.
        :rtype: Dict[str, any]
        """
        return {
            "id": self.id,
            "token": self.ResetToken,
            "employee_id": self.EmployeeID,
            "iss": self.Iss,
            "exp": self.Exp,
            "entry_created": self.EntryCreated
        }

    def as_dict(self):
        """
        A utility method to convert the class attributes into a dictionary format.
        This web friendly version hides the internal IDs, and other metadata information.

        :return: Dictionary representation of the data class attributes.
        :rtype: Dict[str, any]
        """
        return {
            "token": self.ResetToken,
            "employee_id": self.EmployeeID,
            "iss": self.Iss,
            "exp": self.Exp
        }
