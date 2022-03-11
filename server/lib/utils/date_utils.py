from datetime import datetime
from typing import List, Union


def check_date_formats(dates: Union[List[str], str]) -> bool:
    if isinstance(dates, str):
        dates = [dates]
    for date in dates:
        try:
            datetime.strptime(date, '%Y-%m-%d')
            return True
        except ValueError:
            return False
