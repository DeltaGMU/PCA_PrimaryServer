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
        __logging_manager: LoggingManager
        __config_manager = None

        def __new__(cls):
            if cls is Managers:
                raise TypeError(f'The {cls.__name__} class must not be instantiated!')


        @classmethod
        def set_session_manager(cls, session_manager: SessionManager):
            if session_manager is None:
                return
            cls.__session_manager = session_manager

        @classmethod
        def get_session_manager(cls) -> SessionManager:
            return cls.__session_manager

        @classmethod
        def set_web_manager(cls, web_session_manager: WebSessionManager):
            if web_session_manager is None:
                return
            cls.__web_manager = web_session_manager

        @classmethod
        def get_web_manager(cls) -> WebSessionManager:
            return cls.__web_manager

        @classmethod
        def set_logging_manager(cls, logging_manager: LoggingManager):
            if logging_manager is None:
                return
            cls.__logging_manager = logging_manager

        @classmethod
        def get_logging_manager(cls) -> LoggingManager:
            return cls.__logging_manager

        @classmethod
        def set_config_manager(cls, config_manager):
            if config_manager is None:
                return
            cls.__config_manager = config_manager

        @classmethod
        def get_config_manager(cls):
            return cls.__config_manager

    class Settings:
        __debug_mode: bool = False

        def __new__(cls):
            if cls is Settings:
                raise TypeError(f'The {cls.__name__} class must not be instantiated!')

        @classmethod
        def set_debug_mode(cls, debug_mode: bool):
            if debug_mode is None:
                return
            cls.__debug_mode = debug_mode

        @classmethod
        def get_debug_mode(cls) -> bool:
            return cls.__debug_mode
