from typing import Dict, Optional, Any


class ResponseModel:
    """
    This class represents the standard HTTP response model that the API server utilizes
    to respond to HTTP requests. All API responses for this project use this model.
    This response model contains an HTTP status code, HTTP success/error message, and a data field to serve content to front-end interfaces.
    """

    def __init__(self, status: int, message: str, data_dict: Optional[Dict[str, Any]] = None):
        """
        The response model constructor requires an HTTP status code, a status message, and a data dictionary
        with the data that needs to be served to the requestor.

        :param status: The HTTP status code of the response. (Example: 200, 201, 400, 500)
        :type status: int
        :param message: The status message to accompany the HTTP status code. (Example: success/error/warning)
        :type message: str
        :param data_dict: The dictionary that contains the data response to be sent to the requestor.
        :type data_dict: Optional[Dict[str, any]]
        """
        self.status: int = status
        self.message: str = message
        self.data: Dict[str, any] = {}
        if data_dict:
            self.add_data_dict(data_dict)

    def add_data_dict(self, data: Dict[str, any]):
        """
        A method that adds additional data to an existing data dictionary within the response model.

        :param data: A data dictionary to append to the existing content of the response model.
        :type data: Dict[str, any]
        :return: None
        """
        self.data.update(data)

    def update_data(self, name: str, entry: any):
        """
        A method that updates a single data entry in an existing data dictionary within the response model.

        :param name: The field name of the data entry which is also the key in the dictionary.
        :type name: str
        :param entry: The updated data entry that needs to be inserted to the existing data dictionary.
        :type entry: any
        :return: None
        :raises RuntimeError: If the provided data field name does not exist as a key in the response model.
        """
        try:
            self.data[name] = entry
        except KeyError as err:
            raise RuntimeError('The provided key does not exist in the response model data dictionary. Did you mean to append a new data entry instead?') from err

    def as_dict(self):
        """
        Retrieves a dictionary representation of the fields in the response model.
        This is useful when preparing the response model in a JSON compatible format for HTTP responses.

        :return: The dictionary representation of the response model.
        :rtype: Dict[str, any]
        """
        return self.__dict__
