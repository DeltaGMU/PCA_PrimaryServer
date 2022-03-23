#!/usr/bin/python3

"""
The primary initialization python file that initializes the individual core modules
for the server to run.
"""
import signal
import traceback
from config import ENV_SETTINGS
from server.lib.utils.reports_utils import create_reports_directory
from server.lib.web_manager import WebSessionManager
from server.lib.logging_manager import LoggingManager
from server.lib.strings import LOG_ORIGIN_SHUTDOWN, LOG_ORIGIN_GENERAL, LOG_ERROR_GENERAL, LOG_WARNING_GENERAL, LOG_ERROR_UNKNOWN, LOG_ORIGIN_STARTUP
from server.lib.database_access.tables_management_interface import clear_temporary_tables, initialize_tables, initialize_admin


def init():
    """
    Initializes the command-line argument processor and all the core modules for server functionality.
    After initializing all the modules, the server is started.

    :return: None
    """

    """
    parser = argparse.ArgumentParser(
        description="A python-based timesheet/childcare solution with an integrated REST api server "
                    "built for Providence Christian Academy. Developed by Elwis Salinas, Jason Jerome, Elleni Adhanom, "
                    "Robert Gryder, Ramisa Resha, and Dimitrik Johnson as members of "
                    "Team Delta at George Mason University."
    )
    parser._action_groups.pop()
    optional_args = parser.add_argument_group("Optional Arguments")
    logging_args = parser.add_argument_group("Logging Arguments")

    # Launch parameters
    optional_args.add_argument('--host', dest='server_ip', required=False, default=getenv(ENV_MARIADB_HOST),
                               help='Enter the mariadb server IP using this parameter if a .env file is not present.')
    optional_args.add_argument('--port', dest='server_port', required=False, default=getenv(ENV_MARIADB_PORT, 29955),
                               help='Enter the mariadb server port using this parameter if a .env file is not present.')
    optional_args.add_argument('--user', dest='user', required=False, default=getenv(ENV_MARIADB_USER),
                               help='Enter the username of the mariadb account using this parameter if a .env file is not present.')
    optional_args.add_argument('--pass', dest='password', required=False, default=getenv(ENV_MARIADB_PASS),
                               help='Enter the password of the mariadb account using this parameter if a .env file is not present.')
    optional_args.add_argument('--database', dest='db_name', required=False, default=getenv(ENV_MARIADB_DATABASE),
                               help='Enter the name of the mariadb database using this parameter if a .env file is not present.')
    optional_args.add_argument('--web-host', dest='web_ip', required=False, default=getenv(ENV_WEB_HOST),
                               help='Enter the web server IP using this parameter if a .env file is not present.')
    optional_args.add_argument('--web-port', dest='web_port', required=False, default=getenv(ENV_WEB_PORT, 56709),
                               help='Enter the desired REST server port using this parameter if a .env file is not present.')
    optional_args.add_argument('--enable-logs', dest='enable_logs', action='store_true',
                               required=False, default=getenv(ENV_ENABLE_LOGS, 'True'),
                               help='Enables event logging which is useful to locate errors and audit the system.')
    optional_args.add_argument('--debug', dest='sys_debug_mode', action='store_true',
                               required=False, default=getenv(ENV_DEBUG_MODE, 'False'),
                               help='Enables debug mode which prints event messages to the console.')
    optional_args.add_argument('--quiet', dest='quiet_mode', action='store_true',
                               required=False, default=getenv(ENV_QUIET_MODE, 'False'),
                               help='Enables quiet mode which suppresses all server event messages.')

    logging_args.add_argument('--log-level', dest='log_level', required=False, default=getenv(ENV_LOG_LEVEL, "info"),
                              help='Enter the desired log level of logged events using this parameter if a .env file is not present. '
                                   'The following log levels are available to use: [debug, info, warning, error, critical]')
    logging_args.add_argument('--max-logs', dest='max_logs', required=False, default=getenv(ENV_MAX_LOGS, 10),
                              help='Enter the maximum number of log files that can exist at a time using this parameter '
                                   'if a .env file is not present.')
    logging_args.add_argument('--max-log-size', dest='max_log_size', required=False, default=getenv(ENV_MAX_LOG_SIZE, 10485760),
                              help='Enter the maximum size of each log file (in bytes) using this parameter if a .env file is not present.')
    logging_args.add_argument('--log-directory', dest='log_directory', required=False, default=getenv(ENV_LOG_DIRECTORY),
                              help='Enter the default directory to store log files using this parameter if a .env file is not present. '
                                   'If unspecified, the application uses "root/logs" to store log files.')

    args = parser.parse_args()
    args.enable_logs = args.enable_logs.lower() in ('true', '1', 't', 'yes', 'y') if isinstance(args.enable_logs, str) else args.enable_logs
    args.sys_debug_mode = args.sys_debug_mode.lower() in ('true', '1', 't', 'yes', 'y') if isinstance(args.sys_debug_mode, str) else args.sys_debug_mode
    args.quiet_mode = args.quiet_mode.lower() in ('true', '1', 't', 'yes', 'y') if isinstance(args.quiet_mode, str) else args.quiet_mode

    # Ensure that debug mode and quiet mode are both not enabled at the same time.
    sys_debug_mode = bool(args.sys_debug_mode)
    quiet_mode = bool(args.quiet_mode)
    if sys_debug_mode and quiet_mode:
        print("Debug mode and Quiet mode are both enabled, this is a mistake!\nPlease make sure only one or the other is enabled. Defaulting to Quiet mode for this session.")
        sys_debug_mode = False
    """
    web_session_manager = None
    try:
        # Ensure that debug mode and quiet mode are both not enabled at the same time.
        if ENV_SETTINGS.sys_debug_mode and ENV_SETTINGS.quiet_mode:
            print("Debug mode and Quiet mode are both enabled, this is a mistake!\nPlease make sure only one or the other is enabled. Defaulting to Quiet mode for this session.")
            ENV_SETTINGS.sys_debug_mode = False

        LoggingManager().log(LoggingManager.LogLevel.LOG_INFO, 'Initializing PCA Project Server...', origin=LOG_ORIGIN_STARTUP, no_print=False)
        LoggingManager().log(LoggingManager.LogLevel.LOG_INFO, 'System logging manager initialized.', origin=LOG_ORIGIN_STARTUP, no_print=False)
        # Initialize directories for reports.
        create_reports_directory()
        # Initialize any missing tables from the database server.
        initialize_tables()
        # Clear the access/reset Token tables in case the last server shutdown was improper.
        clear_temporary_tables()
        # Initialize the default administrator account if the database contains no administrator accounts.
        initialize_admin()
        # Create and initialize the web session manager with the provided parameters.
        web_session_manager = WebSessionManager(ENV_SETTINGS.web_host, ENV_SETTINGS.web_port)
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
