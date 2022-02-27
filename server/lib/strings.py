"""
DO NOT MODIFY -
The ``strings`` module contains all the metadata and constants that the project requires.
Please do not change any values within this module unless you know what you're doing!
"""
from pathlib import Path

# Project Metadata
META_VERSION = '0.0.1'
META_NAME = 'PCAProject'
ROOT_DIR = Path(__file__).parent.parent

# Core Environment Variable Constants
ENV_MARIADB_USER = 'MARIADB_USER'
ENV_MARIADB_PASS = 'MARIADB_PASS'
ENV_MARIADB_HOST = 'MARIADB_HOST'
ENV_MARIADB_PORT = 'MARIADB_PORT'
ENV_MARIADB_DATABASE = 'MARIADB_DATABASE'
ENV_WEB_HOST = 'WEB_HOST'
ENV_WEB_PORT = 'WEB_PORT'
ENV_DEBUG_MODE = 'DEBUG_MODE'
ENV_QUIET_MODE = 'QUIET_MODE'
ENV_ENABLE_LOGS = 'ENABLE_LOGS'

# Logging Environment Variable Constants
ENV_LOG_LEVEL = 'LOG_LEVEL'
ENV_MAX_LOGS = 'MAX_LOGS'
ENV_MAX_LOG_SIZE = 'MAX_LOG_SIZE'
ENV_LOG_DIRECTORY = 'LOG_DIRECTORY'

# Logging Manager Metadata
LOG_ORIGIN_GENERAL = 'General'
LOG_ORIGIN_API = 'API'
LOG_ORIGIN_DATABASE = 'Database'
LOG_ORIGIN_STARTUP = 'Startup'
LOG_ORIGIN_SHUTDOWN = 'Shutdown'
LOG_ERROR_UNKNOWN = 'Error'
LOG_ERROR_GENERAL = 'Runtime Error'
LOG_WARNING_GENERAL = 'Runtime Warning'
