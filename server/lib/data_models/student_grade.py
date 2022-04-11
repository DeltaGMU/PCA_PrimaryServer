from __future__ import annotations
from pydantic import BaseModel
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Date, LargeBinary, VARCHAR, Boolean, Time, sql
from sqlalchemy.orm import relationship
from server.lib.database_controllers.sqlalchemy_base_interface import MainEngineBase as Base


class PydanticStudentGrade(BaseModel):
    student_grade: str


class StudentGrade(Base):
    """
    A MariaDB data class that represents the table structure of the student grade table in the database server.
    This is replicated in the server code to ensure that the data being sent to and received from the database are valid.
    Do not attempt to manually modify this class or extend it into a subclass.
    """
    __tablename__ = 'student_grade'
    id = Column(Integer, primary_key=True, autoincrement=True, unique=True, nullable=False)
    Name = Column(VARCHAR(length=100), unique=True, nullable=False)
    StudentRelationship = relationship('Student')

    # Do not initialize this except for creating blank student grade templates!
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
