from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.scoping import scoped_session
from config import ENV_SETTINGS
from sqlalchemy.ext.declarative import declarative_base


main_engine = create_engine(
    f"mariadb+mariadbconnector://{ENV_SETTINGS.mariadb_user}:{ENV_SETTINGS.mariadb_pass}@{ENV_SETTINGS.mariadb_host}:{ENV_SETTINGS.mariadb_port}/{ENV_SETTINGS.mariadb_database}",
    echo=ENV_SETTINGS.db_debug_mode,
    pool_recycle=3600
)
MainEngineBase = declarative_base(bind=main_engine)
main_db_session = scoped_session(sessionmaker(bind=main_engine, autoflush=False, autocommit=False))