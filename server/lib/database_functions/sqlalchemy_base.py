from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.scoping import scoped_session
from config import ENV_SETTINGS
from sqlalchemy.ext.declarative import declarative_base

'''
memory_engine = create_engine(
    f"sqlite:///file:tokendb?mode=memory&cache=shared&uri=true",
    echo=ENV_SETTINGS.debug_mode,
    pool_recycle=3600
)
MemoryEngineBase = declarative_base(bind=memory_engine)
memory_db_session = scoped_session(sessionmaker(bind=memory_engine, autoflush=False, autocommit=False))
'''

main_engine = create_engine(
    f"mariadb+mariadbconnector://{ENV_SETTINGS.mariadb_user}:{ENV_SETTINGS.mariadb_pass}@{ENV_SETTINGS.mariadb_host}:{ENV_SETTINGS.mariadb_port}/{ENV_SETTINGS.mariadb_database}",
    echo=ENV_SETTINGS.debug_mode,
    pool_recycle=3600
)
MainEngineBase = declarative_base(bind=main_engine)
main_db_session = scoped_session(sessionmaker(bind=main_engine, autoflush=False, autocommit=False))
