"""
DO NOT MODIFY -
The ``strings`` module contains all the metadata and constants that the project requires.
Please do not change any values within this module unless you know what you're doing!
"""
from pathlib import Path

# Project Metadata
META_VERSION = '1.0.1'
META_NAME = 'PCAProject'
ROOT_DIR = Path(__file__).parent.parent

# Logging Manager Metadata Constants
LOG_ORIGIN_GENERAL = 'General'
LOG_ORIGIN_API = 'API'
LOG_ORIGIN_AUTH = 'Authentication'
LOG_ORIGIN_DATABASE = 'Database'
LOG_ORIGIN_STARTUP = 'Startup'
LOG_ORIGIN_SHUTDOWN = 'Shutdown'
LOG_ERROR_UNKNOWN = 'Error'
LOG_ERROR_GENERAL = 'Runtime Error'
LOG_ERROR_DATABASE = 'Database Error'
LOG_WARNING_GENERAL = 'Runtime Warning'
LOG_WARNING_DATABASE = 'Database Warning'
LOG_WARNING_AUTH = 'Authentication Warning'
