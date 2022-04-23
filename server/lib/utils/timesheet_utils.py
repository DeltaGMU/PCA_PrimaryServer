from math import modf


def round_hours_to_custom_increment(timesheet_hours: float, increment: float = 0.5) -> float:
    """
    This utility method rounds up provided timesheet hours to the provided increment value.
    For example, 0.1 rounds to 0.5, and 0.6 rounds to 1.0

    :param timesheet_hours: The timesheet hours that need to be rounded up by increment amounts.
    :type timesheet_hours: float, required
    :param increment: The increment amount which timesheet hours should be rounded with. The default is 0.5 hour increments.
    :type increment: float, optional
    :return: A floating-point value of the timesheet hours after it has been rounded to the nearest increment value.
    :rtype: float
    """
    if timesheet_hours <= 0:
        return 0
    minutes, hours = modf(timesheet_hours)
    if minutes <= increment:
        if minutes != 0:
            minutes = increment
    else:
        hours += 1
        minutes = 0
    return hours + minutes
