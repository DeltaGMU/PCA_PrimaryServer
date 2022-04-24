"""
This module contains the MariaDB data classes and Pydantic data classes for the student grade entity.
The MariaDB data classes are used in database queries and transactions.
The Pydantic data classes are used in requests to the API for ensuring that data received and sent through requests are valid.
For example, creating a new student grade level record through a request to the API will
require a Pydantic student grade data class to define the attributes needed
to create the student grade level entity in the database and validate the data that is sent in the request.
"""

from __future__ import annotations
from pydantic import BaseModel
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Date, LargeBinary, VARCHAR, Boolean, Time, sql
from sqlalchemy.orm import relationship
from server.lib.database_controllers.sqlalchemy_base_interface import MainEngineBase as Base


class PydanticStudentGrade(BaseModel):
    """
    A Pydantic class used to represent a student grade level when creating a new student grade record from an HTTP request to the API.
    Do not try to initialize this class as an independent entity or extend it into a subclass.
    """
    student_grade: str


class StudentGrade(Base):
    """
    A MariaDB data class that represents the table structure of the student grade table in the database server.
    This model is used to generate the student_grade table in the MariaDB database server.
    """
    __tablename__ = 'student_grade'
    id = Column(Integer, primary_key=True, autoincrement=True, unique=True, nullable=False)
    Name = Column(VARCHAR(length=100), unique=True, nullable=False)
    StudentRelationship = relationship('Student')

    def __init__(self, grade_name: str):
        """
        The constructor for the ``Grade`` data class that is utilized internally by the SQLAlchemy library.
        Only manually instantiate this data class to create employee hours records in the database within database sessions.

        :param grade_name: The grade name.
        :type grade_name: str, required
        """
        self.Name = grade_name

    def as_detail_dict(self):
        """
        A utility method to convert the class attributes into a dictionary format.
        This is useful for representing the entity in a JSON format for a request response.

        :return: Dictionary representation of the data class attributes.
        :rtype: Dict[str, any]
        """
        return {
            "id": self.id,
            "name": self.Name
        }

    def as_dict(self):
        """
        A utility method to convert the class attributes into a dictionary format.
        This web friendly version hides the internal IDs, and other metadata information.

        :return: Dictionary representation of the data class attributes.
        :rtype: Dict[str, any]
        """
        return {
            "name": self.Name
        }
