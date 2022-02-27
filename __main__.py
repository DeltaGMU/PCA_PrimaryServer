"""
The primary initialization python file that handles command-line arguments and initializes the individual core modules
for the server to run.
"""
import signal
import sys
from os import getenv
import argparse
import traceback
from dotenv import load_dotenv
from server.lib.service_manager import SharedData
from server.lib.database_manager import DatabaseManager
from server.lib.web_manager import WebSessionManager
from server.lib.logging_manager import LoggingManager
from server.lib.strings import ENV_MARIADB_HOST, ENV_MARIADB_PORT, ENV_MARIADB_USER, ENV_MARIADB_PASS, \
    ENV_MARIADB_DATABASE, ENV_WEB_HOST, ENV_WEB_PORT, ENV_DEBUG_MODE, ENV_ENABLE_LOGS, ENV_MAX_LOGS, \
    ENV_LOG_LEVEL, ENV_LOG_DIRECTORY, ENV_MAX_LOG_SIZE, LOG_ORIGIN_SHUTDOWN, LOG_ORIGIN_GENERAL, LOG_ERROR_GENERAL, LOG_WARNING_GENERAL, LOG_ERROR_UNKNOWN, ENV_QUIET_MODE, LOG_ORIGIN_STARTUP

load_dotenv()


def init():
    """
    Initializes the command-line argument processor and all the core modules for server functionality.
    After initializing all the modules, the server is started.

    :return: None
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
    optional_args.add_argument('--debug', dest='debug_mode', action='store_true',
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
    args.debug_mode = args.debug_mode.lower() in ('true', '1', 't', 'yes', 'y') if isinstance(args.debug_mode, str) else args.debug_mode
    args.quiet_mode = args.quiet_mode.lower() in ('true', '1', 't', 'yes', 'y') if isinstance(args.quiet_mode, str) else args.quiet_mode

    # Ensure that debug mode and quiet mode are both not enabled at the same time.
    debug_mode = bool(args.debug_mode)
    quiet_mode = bool(args.quiet_mode)
    if debug_mode and quiet_mode:
        print("Debug mode and Quiet mode are both enabled, this is a mistake!\nPlease make sure only one or the other is enabled. Defaulting to Quiet mode for this session.")
        debug_mode = False

    try:
        # Create the project data store for project-related settings and object references.
        shared_data = SharedData()
        shared_data.Settings.set_debug_mode(debug_mode)
        shared_data.Settings.set_quiet_mode(quiet_mode)

        # Create and initialize the logging manager with the provided parameters.
        logging_manager = LoggingManager(bool(args.enable_logs))
        logging_manager.Settings.set_log_level(args.log_level)
        logging_manager.Settings.set_max_logs(int(args.max_logs))
        logging_manager.Settings.set_max_log_size(int(args.max_log_size))
        logging_manager.Settings.set_log_directory(args.log_directory)
        logging_manager.initialize_logging()
        LoggingManager().log(LoggingManager.LogLevel.LOG_INFO, 'Initializing PCA Project Server...', origin=LOG_ORIGIN_STARTUP, no_print=False)

        # Create and initialize the database manager with the provided parameters.
        database_manager = DatabaseManager(args.server_ip, args.server_port, args.db_name,
                                           args.user, args.password)
        shared_data.Managers.set_database_manager(database_manager)

        # Create and initialize the web session manager with the provided parameters.
        web_session_manager = WebSessionManager(args.web_ip, int(args.web_port))
        shared_data.Managers.set_web_manager(web_session_manager)
        # Start the primary web server after all the modules have successfully loaded.
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
        graceful_shutdown()


def graceful_shutdown():
    # Retrieve the web manager object reference and gracefully shutdown the server.
    web_manager_reference = SharedData().Managers.get_web_manager()
    if web_manager_reference:
        web_manager_reference.stop_web_server()
    LoggingManager().log(LoggingManager.LogLevel.LOG_INFO, f'The application has closed.\n{"#" * 140}', origin=LOG_ORIGIN_SHUTDOWN, no_print=False)


def handle_interrupt():
    print("System interrupt detected, shutting down gracefully.")
    graceful_shutdown()


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, handle_interrupt)
    init()
