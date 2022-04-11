from pydantic.main import BaseModel
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Date, LargeBinary, VARCHAR, Boolean, sql
from server.lib.database_controllers.sqlalchemy_base_interface import MainEngineBase as Base
from sqlalchemy.orm import relationship


class PydanticEmployeeRole(BaseModel):
    """
    A Pydantic class used to represent an employee role entity when creating a new employee role record from an HTTP request to the API.
    Do not try to initialize this class as an independent entity or extend it into a subclass.
    """
    role_name: str


class EmployeeRole(Base):
    """
    A MariaDB data class that represents the table structure of the employee role table in the database server.
    This is replicated in the server code to ensure that the data being sent to and received from the database are valid.
    Do not attempt to manually modify this class or extend it into a subclass.
    """
    __tablename__ = 'employee_role'
    id = Column(Integer, primary_key=True, autoincrement=True, unique=True, nullable=False)
    Name = Column(VARCHAR(length=100), unique=True, nullable=False)
    EmployeeRelationship = relationship('Employee')

    def __init__(self, role_name: str):
        """
        The constructor for the ``EmployeeRole`` data class that is utilized internally by the SQLAlchemy library.
        Only manually instantiate this data class to create new employee role records in the database within database sessions.

        :param role_name: The name of the employee role.
        :type role_name: str, required
        """
        self.Name = role_name

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
