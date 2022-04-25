from server.lib.database_controllers.sqlalchemy_base_interface import MainEngineBase, main_engine, main_db_session


class SessionContext:
    """
    The session context class is used to establish temporary sessions with the database.
    These sessions must be retrieved using the ``get_db_session`` utility method.
    """
    def __init__(self, scoped_session_maker):
        self.session = scoped_session_maker()

    def __enter__(self):
        return self.session

    def __exit__(self, exc_type, exc_value, traceback):
        self.session.close()


def get_db_session():
    """
    Creates a session to interface with the database and returns that session.
    Please make sure to close any sessions after finishing queries.

    :return: A new session to the database.
    :rtype: sqlalchemy.orm.Session
    """
    with SessionContext(main_db_session) as session:
        yield session


def get_db_engine():
    """
    Retrieves the database engine.
    Don't use this to make queries to the database, use :func:`~database_manager.get_db_session()` instead.

    :return: Reference to the database engine.
    :rtype: sqlalchemy.engine.Engine
    """
    return main_engine


def is_active() -> bool:
    """
    Checks if the database engine exists.

    :return: True if the database engine exists.
    :rtype: bool
    """
    return main_engine is not None
