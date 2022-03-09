from sqlalchemy.orm.scoping import scoped_session

from server.lib.database_functions.sqlalchemy_base import MemoryEngineBase, memory_engine, memory_db_session


MemoryEngineBase.metadata.create_all(memory_engine)


class SessionContext:
    def __init__(self, scoped_session_maker):
        self.session = scoped_session_maker()

    def __enter__(self):
        return self.session

    def __exit__(self, exc_type, exc_value, traceback):
        self.session.close()


def get_blacklist_session():
    """
    Creates a session to interface with the in-memory database for token blacklisting and returns that session.
    Please make sure to close any sessions after finishing queries.

    :return: A new session to the database.
    :rtype: sqlalchemy.orm.Session
    """
    with SessionContext(memory_db_session) as session:
        yield session


def get_engine():
    """
    Retrieves the in-memory database engine.
    Don't use this to make queries to the in-memory database, use :func:`~token_manager.get_blacklist_session()` instead.

    :return: Reference to the database engine.
    :rtype: sqlalchemy.engine.Engine
    """
    return memory_engine


def is_active() -> bool:
    """
    Checks if the in-memory database engine exists.

    :return: True if the database engine exists.
    :rtype: bool
    """
    return memory_engine is not None
