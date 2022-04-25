"""
This module contains utility functions related to the validation
and formatting of date strings to ensure that a date is compatible with server processes.
"""

from datetime import datetime
from typing import List, Union


def check_date_formats(dates: Union[List[str], str]) -> bool:
    """
    This utility method is used to verify that one or more provided date strings
    are in the YYYY-MM-DD format that the server uses for all date-related functionality.

    :param dates: A list of date strings, or a single date string to be validated.
    :type dates: List[str] | str
    :return: True if all the provided dates are in the YYYY-MM-DD format.
    :rtype: bool
    """
    if dates is None:
        return False
    if isinstance(dates, str):
        dates = [dates]
    for date in dates:
        try:
            datetime.strptime(date, '%Y-%m-%d')
            return True
        except ValueError:
            return False
