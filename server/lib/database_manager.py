from sqlalchemy import create_engine
from sqlalchemy.exc import NoSuchModuleError
from sqlalchemy.orm import sessionmaker
from server.lib.error_codes import ERR_SESSION_MNGR_INCORRECT_PARAMS, ERR_DB_CAUGHT
from server.lib.logging_manager import LoggingManager
from server.lib.service_manager import SharedData
from server.lib.strings import LOG_ORIGIN_STARTUP


class DatabaseManager:
    """
    This class contains the logic to establish a connection to a mariadb database server and
    create sessions where queries can be sent to the database.

    :param server_host: The server IP address of the mariadb database server. (Example: 127.0.0.1)
    :type server_host: str, required
    :param server_port: The port on which the mariadb database server is hosted. (MariaDB Default: 29955)
    :type server_port: str, required
    :param server_db: The name of the database that the database manager should connect to. (Example: my_database)
    :type server_db: str, required
    :param server_user: The username that the database manager should use to establish a connection to the mariadb database server.
    :type server_user: str, required
    :param server_pass: The password that the database manager should use to establish a connection to the mariadb database server.
    :type server_pass: str, required
    :raises RuntimeError: If any of the parameters passed through to the constructor is None.
    """

    def __init__(self,
                 server_host: str,
                 server_port: str,
                 server_db: str,
                 server_user: str,
                 server_pass: str):
        if None in (server_host, server_port, server_db, server_user, server_pass):
            raise RuntimeError(f"Session Manager Error [Error Code: {ERR_SESSION_MNGR_INCORRECT_PARAMS}]\n"
                               "One or more parameters provided to start the service was null!\n"
                               "Please check your .env file or include the missing parameters as startup arguments.\n "
                               "If you are a server administrator, please refer to the software manual!")
        self.server_host = server_host
        self.server_port = server_port
        self.server_db = server_db
        self.server_user = server_user
        self.server_pass = server_pass
        self.db_engine = None
        self.session_factory = None
        self.initialize()

    def initialize(self):
        """
        Initializes the database manager with the connection information provided in the class constructor.
        During the initialization, the database connection is made and the session factory is established.

        :return: None
        :raises RuntimeError: If the database connection cannot be established due to invalid connection parameters.
        """
        try:
            self.db_engine = create_engine(
                f"mariadb+mariadbconnector://{self.server_user}:{self.server_pass}@{self.server_host}:{self.server_port}/{self.server_db}",
                echo=SharedData().Settings.get_debug_mode(),
                pool_recycle=3600
            )
            self.session_factory = sessionmaker(bind=self.db_engine, autoflush=False, autocommit=False)
        except NoSuchModuleError as err:
            raise RuntimeError(f"Database Manager Error [Error Code: {ERR_DB_CAUGHT}]\n"
                               "One or more parameters provided to start the initialize the database connection was invalid!\n"
                               "Please check the username, password, host ip address, port, and database name provided.\n"
                               "If you are a server administrator, please refer to the software manual!") from err
        LoggingManager().log(LoggingManager.LogLevel.LOG_INFO, "Database manager initialized.", origin=LOG_ORIGIN_STARTUP, no_print=False)

    def make_session(self):
        """
        Creates a session to interface with the database and returns that session.
        Please make sure to close any sessions after finishing queries.

        :return: A new session to the database.
        :rtype: sqlalchemy.orm.Session
        """
        return self.session_factory()

    def get_engine(self):
        """
        Retrieves the database engine.
        Don't use this to make queries to the database, use :func:`~database_manager.DatabaseManager.make_session()` instead.

        :return: Reference to the database engine.
        :rtype: sqlalchemy.engine.Engine
        """
        return self.db_engine

    def is_active(self) -> bool:
        """
        Checks if the database engine exists.

        :return: True if the database engine exists.
        :rtype: bool
        """
        return self.db_engine is not None
