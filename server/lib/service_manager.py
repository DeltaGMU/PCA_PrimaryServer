from __future__ import annotations


class SharedData:
    """
    This singleton class manages the state of the multiple manager modules within the application
    that need to be referenced throughout the codebase. In other words, it provides a method of
    referencing these manager modules without the use of traditionally global variables.
    Only one instance of this class may exist at any time and it's subclasses cannot be utilized
    unless the ``SharedData`` class has been initialized.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SharedData, cls).__new__(cls)
        return cls._instance

    @classmethod
    def instance(cls):
        """
        Retrieves the current instance of the SharedData singleton if it has been initialized, otherwise it raises a runtime error.
        Please be sure to initialize the instance by calling the constructor before trying to reference it.

        :return: The current instance of the SharedData singleton if it has been initialized.
        :rtype: SharedData
        :raises Runtime Error: If the ``SharedData`` singleton has not been initialized.
        """
        if cls._instance:
            return cls._instance
        raise RuntimeError('SharedData has not been initialized, call the constructor instead!')

    class Managers:
        """
        This subclass of ``SharedData`` serves as a container for the manager modules of the application.
        It contains utility methods to set/get the manager references.
        """
        __database_manager: DatabaseManager = None
        __web_manager: WebSessionManager = None

        def __new__(cls):
            if cls is Managers:
                raise TypeError(f'The {cls.__name__} class must not be instantiated!')

        @classmethod
        def set_database_manager(cls, database_manager: DatabaseManager):
            """
            Sets the reference to the application's database manager.
            The database manager is responsible for managing the internal connection and interfacing with the mariadb database server.

            :param database_manager: The database manager instance that should be set as a reference.
            :type database_manager: database_manager.DatabaseManager
            :return: None
            """
            if database_manager is None:
                return
            cls.__database_manager = database_manager

        @classmethod
        def get_database_manager(cls) -> DatabaseManager:
            """
            Retrieves the current reference to the application's database manager.
            The database manager is responsible for managing the internal connection and interfacing with the mariadb database server.

            :return: The current database manager reference.
            :rtype: database_manager.DatabaseManager
            """
            return cls.__database_manager

        @classmethod
        def set_web_manager(cls, web_session_manager: WebSessionManager):
            """
            Sets the reference to the application's web session manager.
            The web session manager is responsible for managing and hosting the web server for front-end integration.

            :param web_session_manager: The web session manager instance that should be set as a reference.
            :type web_session_manager: web_manager.WebSessionManager
            :return: None
            """
            if web_session_manager is None:
                return
            cls.__web_manager = web_session_manager

        @classmethod
        def get_web_manager(cls) -> WebSessionManager:
            """
            Retrieves the current reference to the application's web session manager.
            The web session manager is responsible for managing and hosting the web server for front-end integration.

            :return: The current web session manager reference.
            :rtype: web_manager.WebSessionManager
            """
            return cls.__web_manager

    class Settings:
        """
        This subclass of ``SharedData`` serves as a container for the storing runtime application settings.
        It contains utility methods to set/get runtime settings.
        """
        __debug_mode: bool = False
        __quiet_mode: bool = False

        def __new__(cls):
            if cls is Settings:
                raise TypeError(f'The {cls.__name__} class must not be instantiated!')

        @classmethod
        def set_debug_mode(cls, debug_mode: bool):
            """
            Sets the debug mode of the application.
            Enabling debug mode allows the application to log the event messages directly to the console
            in addition to logging it in log files. Enabled debug mode is useful during development
            or trying to find the root cause of bugs.

            :param debug_mode: Enables or disables debug mode for the application.
            :type debug_mode: bool
            :return: None
            """
            if debug_mode is None:
                return
            cls.__debug_mode = debug_mode

        @classmethod
        def get_debug_mode(cls) -> bool:
            """
            Retrieves the current debug mode setting.

            :return: True if debug mode is enabled.
            :rtype: bool
            """
            return cls.__debug_mode

        @classmethod
        def set_quiet_mode(cls, quiet_mode: bool):
            """
            Sets the quiet mode of the application.
            Enabling quiet mode will prevent any events from being logged directly to the console.
            This mode is useful in production environments where server events don't need to be logged to a console.

            :param quiet_mode:
            :type quiet_mode:
            :return: None
            """
            if quiet_mode is None:
                return
            cls.__quiet_mode = quiet_mode

        @classmethod
        def get_quiet_mode(cls) -> bool:
            """
            Retrieves th current quiet mode setting.

            :return: True if quiet mode is enabled.
            :rtype: bool
            """
            return cls.__quiet_mode