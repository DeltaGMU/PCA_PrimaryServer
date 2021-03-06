"""
This module contains the functionality that initializes the MariaDB database server
connection and establishes the required database and required tables if they are not present.
The database connectivity options support both secure and insecure connectivity methods
which are configurable in the server configuration file.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.scoping import scoped_session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_utils import create_database, database_exists

from server.lib.config_manager import ConfigManager
from server.lib.strings import ROOT_DIR

# The database server connection options configured from the server configuration file.
con_opts = {
    "connector": "mariadb+pymysql://",
    "username": ConfigManager().config()['Database']['username'],
    "password": ConfigManager().config()['Database']['password'],
    "host": ConfigManager().config()['Database']['host'],
    "port": int(ConfigManager().config()['Database']['port']),
    "database": ConfigManager().config()['Database']['database_name'],
    "debug": ConfigManager().config().getboolean('Debug Mode', 'db_debug'),
}
ssl_opts = {
    "ssl_ca": f"{ROOT_DIR}/configs/ca-cert.pem"
}
main_engine = create_engine(
    f"{con_opts['connector']}{con_opts['username']}:{con_opts['password']}@{con_opts['host']}:{con_opts['port']}/{con_opts['database']}"
    f"?ssl_ca={ConfigManager().config()['Database']['ca_path']}"
    f"&ssl_check_hostname=false",
    echo=con_opts['debug'],
    pool_recycle=3600,
    pool_pre_ping=True
)
if not database_exists(main_engine.url):
    create_database(main_engine.url)
else:
    main_engine.connect()

MainEngineBase = declarative_base(bind=main_engine)
main_db_session = scoped_session(sessionmaker(bind=main_engine, autoflush=False, autocommit=False))
