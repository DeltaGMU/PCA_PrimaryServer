from __future__ import annotations
import os
import configparser
from server.lib.strings import ROOT_DIR
from server.lib.error_codes import ERR_CONFIG_MNGR_INCORRECT_PARAMS


class ConfigManager:
    """
    This class handles the logic for logging information to both the console and to log files.
    It utilizes rotating log files to log server processes and events as well as any errors that may occur.

    :raises RuntimeError: If any of the parameters passed through to the constructor is invalid.
    """

    _instance = None
    __config = None

    def __new__(cls, config_path: str = None):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            if cls.__config is None:
                cls.__config = configparser.ConfigParser()
                if config_path and os.path.exists(config_path):
                    cls.__config.read(config_path)
                else:
                    raise RuntimeError(f"Config Manager Error [Error Code: {ERR_CONFIG_MNGR_INCORRECT_PARAMS}]\n"
                                       "One or more parameters provided to start the service was null!\n"
                                       "Please check the server config file exists and the path provided is correct.\n "
                                       "If you are a server administrator, please refer to the software manual!")
        return cls.instance()

    @classmethod
    def instance(cls):
        """
        Retrieves an instance of the current config manager instance or raises an error if the manager has not been initialized yet.

        :return: The instance of the config manager.
        :rtype: ConfigManager
        :raises RuntimeError: If the config manager is not initialized.
        """
        if cls._instance:
            return cls._instance
        raise RuntimeError('Config Manager class has not been instantiated, call the constructor instead!')

    @classmethod
    def config(cls):
        """
        Retrieves an instance of the current config or raises an error if the manager has not been initialized yet.

        :return: The instance of the config.
        :rtype: configparser
        :raises RuntimeError: If the config instance is not initialized.
        """
        if cls._instance and cls.__config:
            return cls.__config
        raise RuntimeError('Config instance has not been instantiated, call the constructor instead!')

    @classmethod
    def save(cls):
        """
        Saves the current configuration to the server config file.

        :raise RuntimeError: If the config manager is not initialized.
        """
        if cls._instance:
            with open(f'{ROOT_DIR}/configs/server_config.ini') as fh:
                cls.__config.write(fh)
        raise RuntimeError('Config Manager class has not been instantiated, call the constructor instead!')

    @classmethod
    def validate(cls):
        """
        Validates the current configuration file to ensure all the required fields are present.

        :raise RuntimeError: If the server config file is missing any critical options.
        """
        if cls._instance:
            config = cls._instance.config()
            try:
                config.get('Database', 'username')
                config.get('Database', 'password')
                config.get('Database', 'host')
                config.get('Database', 'port')
                config.get('Database', 'database_name')
                config.get('API Server', 'host')
                config.get('API Server', 'port')
                config.get('API Server', 'use_https')
                config.get('API Server', 'ca_path')
                config.get('API Server', 'key_path')
                config.get('API Server', 'cors_domains')
                config.get('API Server', 'server_secret')
                config.get('API Server', 'enable_docs')
                config.get('API Server', 'cert_path')
                config.get('Debug Mode', 'sys_debug')
                config.get('Debug Mode', 'api_debug')
                config.get('Debug Mode', 'db_debug')
                config.get('Debug Mode', 'quiet_mode')
                config.get('Logging', 'enable_logs')
                config.get('Logging', 'log_level')
                config.get('Logging', 'max_logs')
                config.get('Logging', 'max_log_size')
                config.get('Logging', 'log_directory')
                config.get('Student Care Settings', 'before_care_check_in_time')
                config.get('Student Care Settings', 'before_care_check_out_time')
                config.get('Student Care Settings', 'after_care_check_in_time')
                config.get('Student Care Settings', 'after_care_check_out_time')
                config.get('System Settings', 'account_roles')
                config.get('System Settings', 'leave_request_reasons')
                config.get('System Settings', 'leave_request_mailing_address')
                config.get('Security Settings', 'access_token_expiry_minutes')
                config.get('Security Settings', 'reset_code_expiry_minutes')
                config.get('Email Settings', 'pca_email_api')
                config.get('Email Settings', 'pca_email_use_https')
                config.get('Email Settings', 'pca_email_username')
                config.get('Email Settings', 'pca_email_password')
                return True
            except configparser.NoSectionError as err:
                raise RuntimeError(f"Error encountered validating server configuration file. "
                                   f"Please ensure that there are no missing sections! "
                                   f"{str(err)}")
            except configparser.NoOptionError as err:
                raise RuntimeError(f"Error encountered validating server configuration file. "
                                   f"Please ensure that there are no missing fields! "
                                   f"{str(err)}")


# Create and initialize the config manager with the server_config.ini path.
try:
    config_manager = ConfigManager(f"{ROOT_DIR}/configs/server_config.dev.ini")
except FileNotFoundError:
    config_manager = ConfigManager(f"{ROOT_DIR}/configs/server_config.ini")
