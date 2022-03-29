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


# Create and initialize the config manager with the server_config.ini path.
config_manager = ConfigManager(f"{ROOT_DIR}/configs/server_config.ini")
