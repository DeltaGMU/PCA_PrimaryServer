from __future__ import annotations
import logging
from typing import Union, List
from enum import Enum, unique
from os import path, makedirs
from logging.handlers import RotatingFileHandler
from server.lib.config_manager import ConfigManager
from server.lib.utils.print_utils import debug_print
from server.lib.strings import ROOT_DIR, META_NAME, META_VERSION, LOG_ORIGIN_GENERAL, LOG_ORIGIN_STARTUP
from server.lib.error_codes import ERR_LOGGING_MNGR_INCORRECT_PARAMS


class LoggingManager:
    """
    This class handles the logic for logging information to both the console and to log files.
    It utilizes rotating log files to log server processes and events as well as any errors that may occur.

    :param enable_logging: Enable or disable logging for the current session.
    :type enable_logging: bool, optional
    :raises RuntimeError: If any of the parameters passed through to the constructor is None.
    """

    _instance = None
    __logger = None
    __enable_logging = False

    def __new__(cls, enable_logging: bool = False):
        if cls._instance is None:
            if enable_logging is None:
                raise RuntimeError(f"Logging Manager Error [Error Code: {ERR_LOGGING_MNGR_INCORRECT_PARAMS}]\n"
                                   "One or more parameters provided to start the service was null!\n"
                                   "Please check your server config file or include the missing parameters as startup arguments.\n "
                                   "If you are a server administrator, please refer to the software manual!")
            cls._instance = super(LoggingManager, cls).__new__(cls)
            cls.__logger = None
            cls.__enable_logging = False

            if not path.exists(ConfigManager().config()['Logging']['log_directory']):
                makedirs(ConfigManager().config()['Logging']['log_directory'])
            if enable_logging:
                cls._instance.enable()
        return cls.instance()

    @classmethod
    def instance(cls):
        """
        Retrieves an instance of the current logging manager instance or raises an error if the manager has not been initialized yet.

        :return: The instance of the logging manager.
        :rtype: LoggingManager
        """
        if cls._instance:
            return cls._instance
        raise RuntimeError('Logging Manager class has not been instantiated, call the constructor instead!')

    @classmethod
    def initialize_logging(cls):
        """
        Initializes the logger library with a rotating file handler and the parameters provided.
        Make sure the logging manager is initialized before initializing logging.

        :return: None
        :raises RuntimeError: If the logging manager has not been initialized.
        """
        if not cls._instance:
            raise RuntimeError('Logging Manager class has not been instantiated, please instantiate the class first!')
        if not cls._instance.is_enabled():
            return

        cls._instance.__logger = logging.getLogger("PCARuntimeLogging")
        cls._instance.__logger.setLevel(cls._instance.LogLevel.LOG_DEBUG.value[0])
        cls._instance.__logger.handlers = []

        log_file_name = f"{ConfigManager().config()['Logging']['log_directory']}/runtime.log"
        handler = RotatingFileHandler(
            log_file_name,
            maxBytes=int(ConfigManager().config()['Logging']['max_log_size']),
            backupCount=int(ConfigManager().config()['Logging']['max_logs'])
        )
        handler.setFormatter(logging.Formatter('[%(asctime)s]-[%(levelname)s]-%(message)s'))
        cls._instance.__logger.addHandler(handler)

    @classmethod
    def log(cls, log_type: LoggingManager.LogLevel, message: Union[List[str], str], origin: str = None, error_type: str = None,
            no_print: bool = True, exc_message: str = None):
        """
        The primary method used to log messages to the application log files and to the console output.
        Utilize this method instead of print() or any other built-in method to display messages in the console.

        :param log_type: The log level of the logger (debug, info, warning, error, critical)
        :type log_type: LoggingManager.LogLevel, required
        :param message: The message that must be logged or printed by the application.
        :type message: Union[List[str], str], required
        :param origin: The origin of the event that needs to be logged. Please refer to the :mod:`strings` module for a list of defined log origins.
        :type origin: str, optional
        :param error_type: If logging an error, the type of error that is being logged. Please refer to the :mod:`error_codes` module for a list of defined error types.
        :type error_type: str, optional
        :param no_print: Set to false if the message being logged should also be printed to the console.
        :type no_print: bool, optional
        :param exc_message: If logging an error, the exception stack trace should be passed here as a string.
        :type exc_message: str, optional
        :return: None
        """
        if cls._instance is None:
            return
        # If an event is trying to be logged but the logger is disabled, raise an error.
        if not cls._instance.is_enabled():
            return
        # If logging is enabled, and the log service is missing, raise an error.
        if cls._instance.__logger is None:
            raise RuntimeError('Error: Logging is enabled but the logger has not been initialized.')
        if None in (log_type, message):
            raise RuntimeError('Error: One or more required parameters to log events was missing.')
        # If the provided log message is not a list, convert it to a list for simpler processing later.
        if not isinstance(message, list):
            message = [message]
        # Format the log messages for outputting.
        log_message = "\n".join(message) if len(message) > 1 else message[0]

        # Format the message and log the event as necessary.
        log_output = f'[{META_NAME}({META_VERSION}).{origin if origin else LOG_ORIGIN_GENERAL}]' \
                     f'{f"<{error_type}>:" if error_type else ""} {log_message}'
        # If an exception stack trace is provided, include the stack trace in the log message.
        if exc_message:
            log_output += f"\n{exc_message}\n"
        # Log the formatted message based on the log level.
        if log_type == cls._instance.LogLevel.LOG_INFO:
            cls._instance.__logger.info(log_output)
        elif log_type == cls._instance.LogLevel.LOG_DEBUG:
            cls._instance.__logger.debug(log_output)
        elif log_type == cls._instance.LogLevel.LOG_WARNING:
            cls._instance.__logger.warning(log_output)
        elif log_type == cls._instance.LogLevel.LOG_ERROR:
            cls._instance.__logger.error(log_output)
        elif log_type == cls._instance.LogLevel.LOG_CRITICAL:
            cls._instance.__logger.critical(log_output)
        else:
            raise RuntimeError('Error: The logger tried to log a message with an invalid log level!')
        # After logging the event, print the message to the console if printing is allowed.
        if not no_print:
            debug_print(log_message, origin=origin, error_type=error_type)

    @classmethod
    def get_logger(cls) -> logging.Logger | None:
        """
        Retrieves the logger from the current active logging manager instance.

        :return: The logger from the current instance, or None if it has not been initialized.
        :rtype: logging.Logger | None
        """
        if cls._instance is None:
            return None
        return cls._instance.__logger

    @classmethod
    def is_enabled(cls) -> bool | None:
        """
        Checks if logging is enabled or disabled in the logging manager.

        :return: True if logging is enabled, False if logging is disabled, or None if the instance is not initialized.
        :rtype: bool | None
        """
        if cls._instance:
            return cls._instance.__enable_logging
        return None

    @classmethod
    def enable(cls):
        """
        Enables logging in the logging manager if the instance is initialized.

        :return: None
        """
        if cls._instance:
            cls._instance.__enable_logging = True

    @classmethod
    def disable(cls):
        """
        Disables logging in the logging manager if the instance is initialized.
        Disabling logging will prevent messages and events from being logged in the application log files or displayed in the console.

        :return: None
        """
        if cls._instance:
            cls._instance.__enable_logging = False

    @unique
    class LogLevel(Enum):
        """
        This enum class defines the types of log levels available for the logging library to use.
        Do not modify this unless you know what you're doing!
        """
        LOG_DEBUG = 10, 'debug'
        LOG_INFO = 20, 'info'
        LOG_WARNING = 30, 'warning'
        LOG_ERROR = 40, 'error'
        LOG_CRITICAL = 50, 'critical'

        @classmethod
        def has_value_id(cls, value: int) -> Union[(int, str), None]:
            """
            This utility method checks if the given enum integer value is present in the Log Level tuple values.

            :param value: The integer value to check in the Log Level enum.
            :type value: int
            :return: A tuple containing the integer value of the enum and the string representation.
            :rtype: (int, str) | None
            """
            for item in cls._value2member_map_:
                if value == item[0]:
                    return item
            return None

        @classmethod
        def has_value_label(cls, value: str) -> Union[(int, str), None]:
            """
            This utility method checks if the given enum string value is present in the Log Level tuple values.

            :param value: The string value to check in the Log Level enum.
            :type value: str
            :return: A tuple containing the integer value of the enum and the string representation.
            :rtype: (int, str) | None
            """
            for item in cls._value2member_map_:
                if value == item[1]:
                    return item
            return None


# Create and initialize the logging manager with the provided parameters.
logging_manager = LoggingManager(ConfigManager().config()['Logging']['enable_logs'])
logging_manager.initialize_logging()
