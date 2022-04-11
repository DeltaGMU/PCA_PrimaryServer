#!/usr/bin/python3

"""
The primary initialization python file that initializes the individual core modules
for the server to run.
"""
import signal
import traceback

from server.lib.config_manager import ConfigManager
from server.lib.web_manager import WebSessionManager
from server.lib.logging_manager import LoggingManager
from server.lib.strings import LOG_ORIGIN_SHUTDOWN, LOG_ORIGIN_GENERAL, LOG_ERROR_GENERAL, LOG_WARNING_GENERAL, LOG_ERROR_UNKNOWN, LOG_ORIGIN_STARTUP
from server.lib.database_controllers.tables_management_interface import clear_temporary_tables, initialize_tables, initialize_admin


def init():
    """
    Initializes the command-line argument processor and all the core modules for server functionality.
    After initializing all the modules, the server is started.

    :return: None
    """

    web_session_manager = None
    try:
        # Ensure that debug mode and quiet mode are both not enabled at the same time.
        if ConfigManager().config().getboolean('Debug Mode', 'sys_debug') and ConfigManager().config().getboolean('Debug Mode', 'quiet_mode'):
            print("Debug mode and Quiet mode are both enabled, this is a mistake!\nPlease make sure only one or the other is enabled. Defaulting to Quiet mode for this session.")
            ConfigManager().config()['Debug Mode']['sys_debug'] = False

        LoggingManager().log(LoggingManager.LogLevel.LOG_INFO, 'Initializing PCA Project Server...', origin=LOG_ORIGIN_STARTUP, no_print=False)
        LoggingManager().log(LoggingManager.LogLevel.LOG_INFO, 'System logging manager initialized.', origin=LOG_ORIGIN_STARTUP, no_print=False)
        # Initialize any missing tables from the database server.
        initialize_tables()
        # Clear the access/reset Token tables in case the last server shutdown was improper.
        clear_temporary_tables()
        # Initialize the default administrator account if the database contains no administrator accounts.
        initialize_admin()
        # Create and initialize the web session manager with the provided parameters.
        web_session_manager = WebSessionManager(ConfigManager().config()['API Server']['host'], int(ConfigManager().config()['API Server']['port']))
        # Start the primary web server after all the modules have successfully been configured.
        web_session_manager.start_web_server()
    except RuntimeError as err:
        LoggingManager().log(LoggingManager.LogLevel.LOG_CRITICAL, f"{str(err)}", origin=LOG_ORIGIN_GENERAL, error_type=LOG_ERROR_GENERAL,
                             exc_message=traceback.format_exc(), no_print=False)
        raise RuntimeError("Oh no! Encountered a fatal error!") from err
    except RuntimeWarning as warn:
        LoggingManager().log(LoggingManager.LogLevel.LOG_WARNING, f"Runtime Warning: {str(warn)}", origin=LOG_ORIGIN_GENERAL, error_type=LOG_WARNING_GENERAL,
                             exc_message=traceback.format_exc(), no_print=False)
        raise RuntimeWarning("Warning: Encountered a non-critical error.") from warn
    except BaseException as unknown_err:
        LoggingManager().log(LoggingManager.LogLevel.LOG_CRITICAL, f"{str(unknown_err)}", origin=LOG_ORIGIN_GENERAL, error_type=LOG_ERROR_UNKNOWN,
                             exc_message=traceback.format_exc(), no_print=False)
        raise Exception("Error: Encountered a critical error.") from unknown_err
    finally:
        graceful_shutdown(web_session_manager)


def graceful_shutdown(web_session_manager=None):
    # Retrieve the web manager object reference and gracefully shutdown the server.
    if web_session_manager:
        web_session_manager.stop_web_server()
    # Clear the access/reset Token tables if the server is being shutdown.
    clear_temporary_tables()
    LoggingManager().log(LoggingManager.LogLevel.LOG_INFO, f'The application has closed.\n{"#" * 140}', origin=LOG_ORIGIN_SHUTDOWN, no_print=False)


def handle_interrupt():
    print("System interrupt detected, shutting down gracefully.")
    graceful_shutdown()


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, handle_interrupt)
    init()
