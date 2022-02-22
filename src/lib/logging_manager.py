from __future__ import annotations
import traceback
import logging
from typing import Union, List
from enum import Enum, unique, EnumMeta
from os import listdir, path, makedirs, unlink
from logging.handlers import RotatingFileHandler
from src.lib.utils.print_utils import debug_print
from src.lib.strings import ROOT_DIR, META_NAME, META_VERSION, LOG_ORIGIN_GENERAL, LOG_ORIGIN_STARTUP
from src.lib.error_codes import ERR_LOGGING_MNGR_INCORRECT_PARAMS


class LoggingManager:
    _instance = None
    __enable_logging = False
    __logger = None

    def __new__(cls, enable_logging: bool = False):
        if cls._instance is None:
            if enable_logging is None:
                raise RuntimeError(f"Logging Manager Error [Error Code: {ERR_LOGGING_MNGR_INCORRECT_PARAMS}]\n"
                                   "One or more parameters provided to start the service was null!\n"
                                   "Please check your .env file or include the missing parameters as startup arguments.\n "
                                   "If you are a server administrator, please refer to the software manual!")
            cls._instance = super(LoggingManager, cls).__new__(cls)

            if not path.exists(f"{ROOT_DIR}/logs"):
                makedirs(f"{ROOT_DIR}/logs")
            if enable_logging:
                cls._instance.enable()
        return cls._instance

    @classmethod
    def instance(cls):
        if cls._instance:
            return cls._instance
        raise RuntimeError('Logging Manager class has not been instantiated, call the constructor instead!')

    @classmethod
    def initialize_logging(cls):
        if not cls._instance:
            raise RuntimeError('Logging Manager class has not been instantiated, please instantiate the class first!')
        if not cls._instance.is_enabled():
            return
        cls._instance.__logger = logging.getLogger("PCARuntimeLogging")
        cls._instance.__logger.setLevel(cls._instance.LogLevel.LOG_DEBUG.value[0])

        log_file_name = f"{ROOT_DIR}/logs/runtime.log"
        handler = RotatingFileHandler(
            log_file_name,
            maxBytes=cls._instance.Settings.get_max_log_size(),
            backupCount=cls._instance.Settings.get_max_logs()
        )
        handler.setFormatter(logging.Formatter('[%(asctime)s]-[%(levelname)s]-%(message)s'))
        cls._instance.__logger.addHandler(handler)
        cls._instance.log(cls._instance.LogLevel.LOG_INFO, 'Logging manager initialized.', origin=LOG_ORIGIN_STARTUP, no_print=False)

    @classmethod
    def log(cls, log_type: LoggingManager.LogLevel, message: Union[List[str], str], origin: str = None, error_type: str = None,
            no_print: bool = True):
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
                     f'{f"<{error_type}>:" if error_type else ""}{log_message}'
        # If log stack tracing is enabled, include the stack trace in the log message.
        # Please note that enabling stack tracing results in significantly larger log messages.
        if cls._instance.Settings.get_log_trace():
            log_output += f"\n{''.join(traceback.format_stack())}\n"
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
        if cls._instance is None:
            return None
        return cls._instance.__logger

    @classmethod
    def is_enabled(cls) -> bool | None:
        if cls._instance:
            return cls._instance.__enable_logging
        return None

    @classmethod
    def enable(cls):
        if cls._instance:
            cls._instance.__enable_logging = True

    @classmethod
    def disable(cls):
        if cls._instance:
            cls._instance.__enable_logging = False

    @unique
    class LogLevel(Enum):
        LOG_DEBUG = 10, 'debug'
        LOG_INFO = 20, 'info'
        LOG_WARNING = 30, 'warning'
        LOG_ERROR = 40, 'error'
        LOG_CRITICAL = 50, 'critical'

        @classmethod
        def has_value_id(cls, value: int) -> (int, str):
            for item in cls._value2member_map_:
                if value == item[0]:
                    return item
            return None

        @classmethod
        def has_value_label(cls, value: str) -> (int, str):
            for item in cls._value2member_map_:
                if value == item[1]:
                    return item
            return None

    class Settings:
        __log_level: LoggingManager.LogLevel = None
        __log_trace: bool = False
        __max_logs: int = 10
        __max_log_size: int = 10*1024*1024
        __log_directory: str = f'{ROOT_DIR}/logs'

        def __new__(cls):
            if cls is LoggingManager.Settings:
                raise TypeError(f'The {cls.__name__} class must not be instantiated!')

        @classmethod
        def set_log_directory(cls, log_directory: str):
            if log_directory is None:
                return
            cls.__log_directory = log_directory

        @classmethod
        def get_log_directory(cls) -> str:
            return cls.__log_directory

        @classmethod
        def set_log_level(cls, log_level: LoggingManager.LogLevel | str | int):
            if isinstance(log_level, str):
                log_level_item = LoggingManager.LogLevel.has_value_label(log_level)
                if log_level_item:
                    cls.__log_level = LoggingManager.LogLevel(log_level_item)
                    return
            elif isinstance(log_level, int):
                log_level_item = LoggingManager.LogLevel.has_value_id(log_level)
                if log_level_item:
                    cls.__log_level = LoggingManager.LogLevel(log_level_item)
                    return
            elif isinstance(log_level, LoggingManager.LogLevel):
                cls.__log_level = log_level
                return
            raise RuntimeError(f'Error: The logging level was attempted to be changed, however the provided log level was invalid: '
                               f'{log_level}[{type(log_level)}]\nThe log level must be of type: LoggingManager.LogLevel')

        @classmethod
        def get_log_level(cls) -> LoggingManager.LogLevel:
            return cls.__log_level

        @classmethod
        def set_log_trace(cls, log_trace: bool):
            if log_trace is None:
                return
            cls.__log_trace = log_trace

        @classmethod
        def get_log_trace(cls) -> bool:
            return cls.__log_trace

        @classmethod
        def set_max_logs(cls, max_logs: int):
            if max_logs is None:
                return
            max_logs = max(1, max_logs)
            cls.__max_logs = max_logs

        @classmethod
        def get_max_logs(cls) -> int:
            return cls.__max_logs

        @classmethod
        def set_max_log_size(cls, max_size: int):
            if max_size is None:
                return
            max_size = max(65536, max_size)
            cls.__max_log_size = max_size

        @classmethod
        def get_max_log_size(cls) -> int:
            return cls.__max_log_size
