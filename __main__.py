from os import getenv
from sys import exit
import argparse
import traceback
from dotenv import load_dotenv
from src.lib.service_manager import SharedData
from src.lib.database_manager import DatabaseManager, WebSessionManager
from src.lib.logging_manager import LoggingManager
from src.lib.strings import ENV_MARIADB_HOST, ENV_MARIADB_PORT, ENV_MARIADB_USER, ENV_MARIADB_PASS, \
    ENV_MARIADB_DATABASE, ENV_WEB_HOST, ENV_WEB_PORT, ENV_DEBUG_MODE, ENV_ENABLE_LOGS, ENV_LOG_TRACE, ENV_MAX_LOGS, \
    ENV_LOG_LEVEL, ENV_LOG_DIRECTORY, ENV_MAX_LOG_SIZE, LOG_ORIGIN_SHUTDOWN, LOG_ORIGIN_GENERAL, LOG_ERROR_GENERAL, LOG_WARNING_GENERAL

load_dotenv()


def init():
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
    optional_args.add_argument('--port', dest='server_port', required=False, default=getenv(ENV_MARIADB_PORT),
                               help='Enter the mariadb server port using this parameter if a .env file is not present.')
    optional_args.add_argument('--user', dest='user', required=False, default=getenv(ENV_MARIADB_USER),
                               help='Enter the username of the mariadb account using this parameter if a .env file is not present.')
    optional_args.add_argument('--pass', dest='password', required=False, default=getenv(ENV_MARIADB_PASS),
                               help='Enter the password of the mariadb account using this parameter if a .env file is not present.')
    optional_args.add_argument('--database', dest='db_name', required=False, default=getenv(ENV_MARIADB_DATABASE),
                               help='Enter the name of the mariadb database using this parameter if a .env file is not present.')
    optional_args.add_argument('--web-host', dest='web_ip', required=False, default=getenv(ENV_WEB_HOST),
                               help='Enter the web server IP using this parameter if a .env file is not present.')
    optional_args.add_argument('--web-port', dest='web_port', required=False, default=getenv(ENV_WEB_PORT),
                               help='Enter the desired REST server port using this parameter if a .env file is not present.')
    optional_args.add_argument('--enable-logs', dest='enable_logs', action='store_true',
                               required=False, default=getenv(ENV_ENABLE_LOGS, 'True'),
                               help='Enables event logging which is useful to locate errors and audit the system.')
    optional_args.add_argument('--debug', dest='debug_mode', action='store_true',
                               required=False, default=getenv(ENV_DEBUG_MODE, 'False'),
                               help='Enables debug mode which prints event messages to the console.')

    logging_args.add_argument('--log-trace', dest='log_trace', action='store_true',
                               required=False, default=getenv(ENV_LOG_TRACE, 'False'),
                               help='Enables log stack tracing which includes the stack trace of logged events.')
    logging_args.add_argument('--log-level', dest='log_level', required=False, default=getenv(ENV_LOG_LEVEL),
                              help='Enter the desired log level of logged events using this parameter if a .env file is not present. '
                                   'The following log levels are available to use: [debug, info, warning, error, critical]')
    logging_args.add_argument('--max-logs', dest='max_logs', required=False, default=getenv(ENV_MAX_LOGS),
                              help='Enter the maximum number of log files that can exist at a time using this parameter '
                                   'if a .env file is not present.')
    logging_args.add_argument('--max-log-size', dest='max_log_size', required=False, default=getenv(ENV_MAX_LOG_SIZE),
                              help='Enter the maximum size of each log file (in bytes) using this parameter if a .env file is not present.')
    logging_args.add_argument('--log-directory', dest='log_directory', required=False, default=getenv(ENV_LOG_DIRECTORY),
                              help='Enter the default directory to store log files using this parameter if a .env file is not present. '
                                   'If unspecified, the application uses "root/logs" to store log files.')

    args = parser.parse_args()
    args.enable_logs = args.enable_logs.lower() in ('true', '1', 't', 'yes', 'y') if isinstance(args.enable_logs, str) else args.enable_logs
    args.debug_mode = args.debug_mode.lower() in ('true', '1', 't', 'yes', 'y') if isinstance(args.debug_mode, str) else args.debug_mode
    args.log_trace = args.log_trace.lower() in ('true', '1', 't', 'yes', 'y') if isinstance(args.log_trace, str) else args.log_trace

    try:
        shared_data = SharedData()
        shared_data.Settings.set_debug_mode(bool(args.debug_mode))

        logging_manager = LoggingManager(bool(args.enable_logs))
        logging_manager.Settings.set_log_level(args.log_level)
        logging_manager.Settings.set_log_trace(bool(args.log_trace))
        logging_manager.Settings.set_max_logs(int(args.max_logs))
        logging_manager.Settings.set_max_log_size(int(args.max_log_size))
        logging_manager.Settings.set_log_directory(args.log_directory)
        logging_manager.initialize_logging()
        shared_data.Managers.set_logging_manager(logging_manager)

        database_manager = DatabaseManager(args.server_ip, args.server_port, args.db_name,
                                          args.user, args.password)
        shared_data.Managers.set_database_manager(database_manager)

        web_session_manager = WebSessionManager(args.web_ip, int(args.web_port))
        shared_data.Managers.set_web_manager(web_session_manager)
    except RuntimeError as err:
        LoggingManager().log(LoggingManager.LogLevel.LOG_CRITICAL, f"Runtime Error: {str(err)}\n{traceback.print_exc()}", origin=LOG_ORIGIN_GENERAL, error_type=LOG_ERROR_GENERAL, no_print=False)
        raise RuntimeError("Oh no! Encountered a fatal error!") from err
    except RuntimeWarning as warn:
        LoggingManager().log(LoggingManager.LogLevel.LOG_WARNING, f"Runtime Warning: {str(warn)}\n{traceback.print_exc()}", origin=LOG_ORIGIN_GENERAL, error_type=LOG_WARNING_GENERAL, no_print=False)
        raise RuntimeWarning("Warning: Encountered a non-critical error.") from warn
    finally:
        LoggingManager().log(LoggingManager.LogLevel.LOG_INFO, f'The application has closed.\n{"#"*60}', origin=LOG_ORIGIN_SHUTDOWN, no_print=False)


if __name__ == "__main__":
    init()
