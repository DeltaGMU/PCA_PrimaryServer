from __future__ import annotations


class SharedData:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SharedData, cls).__new__(cls)
        return cls._instance

    def instance(cls):
        if cls._instance:
            return cls._instance
        raise RuntimeError('SharedData has not been initialized, call the constructor instead!')

    class Managers:
        __session_manager: SessionManager
        __web_manager: WebSessionManager
        __config_manager = None

        @classmethod
        def set_session_manager(cls, session_manager: SessionManager):
            cls.__session_manager = session_manager

        @classmethod
        def get_session_manager(cls) -> SessionManager:
            return cls.__session_manager

        @classmethod
        def set_web_manager(cls, web_session_manager: WebSessionManager):
            cls.__web_manager = web_session_manager

        @classmethod
        def get_web_manager(cls) -> WebSessionManager:
            return cls.__web_manager

        @classmethod
        def set_config_manager(cls, config_manager):
            cls.__config_manager = config_manager

        @classmethod
        def get_config_manager(cls):
            return cls.__config_manager

    class Settings:
        __debug_mode: bool = False
        __logging_mode: str = "info"

        @classmethod
        def set_debug_mode(cls, debug_mode: bool):
            cls.__debug_mode = debug_mode

        @classmethod
        def get_debug_mode(cls) -> bool:
            return cls.__debug_mode

        @classmethod
        def set_logging_mode(cls, logging_mode: str):
            cls.__logging_mode = logging_mode

        @classmethod
        def get_logging_mode(cls) -> str:
            return cls.__logging_mode

