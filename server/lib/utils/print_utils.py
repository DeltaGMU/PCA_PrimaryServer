"""
The print utility module contains multiple utility methods that serve to help tasks related to displaying console output messages.
For example, the ``console_print`` utility method can be used to display a message to the console if the application is not in debug mode.
"""

from server.lib.strings import META_NAME, META_VERSION, LOG_ORIGIN_GENERAL
from config import ENV_SETTINGS


def debug_print(message: str, origin: str = None, error_type: str = None):
    """
    An internal method used to display a message to the console output if the application
    is running in debug mode and NOT quiet mode.
    Do not use this method during development to print to the console, instead
    use :func:`~logging_manager.LoggingManager.log()` to log and display messages.

    :param message: The message to be displayed in the console output.
    :type message: str, required
    :param origin: The origin of the message that needs to be displayed. Please refer to the :mod:`strings` module for a list of defined origins.
    :type origin: str, optional
    :param error_type: If displaying an error, the type of error that is being displayed. Please refer to the :mod:`error_codes` module for a list of defined error types.
    :type error_type: str, optional
    :return: None
    """
    if ENV_SETTINGS.sys_debug_mode and not ENV_SETTINGS.quiet_mode:
        print(f'[{META_NAME}({META_VERSION}).{origin if origin else LOG_ORIGIN_GENERAL}]'
              f'{f"<{error_type}>:" if error_type else ""} {message}')


def console_print(message: str, origin: str = None, error_type: str = None):
    """
    An internal method used to display a message to the console output if the application
    is NOT running in debug mode or quiet mode.
    Do not use this method during development to print to the console, instead
    use :func:`~logging_manager.LoggingManager.log()` to log and display messages.

    :param message: The message to be displayed in the console output.
    :type message: str, required
    :param origin: The origin of the message that needs to be displayed. Please refer to the :mod:`strings` module for a list of defined origins.
    :type origin: str, optional
    :param error_type: If displaying an error, the type of error that is being displayed. Please refer to the :mod:`error_codes` module for a list of defined error types.
    :type error_type: str, optional
    :return: None
    """
    if not ENV_SETTINGS.sys_debug_mode and not ENV_SETTINGS.quiet_mode:
        print(f'[{META_NAME}({META_VERSION}).{origin if origin else LOG_ORIGIN_GENERAL}]'
              f'{f"<{error_type}>:" if error_type else ""} {message}')
