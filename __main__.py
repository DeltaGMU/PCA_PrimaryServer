from src.services.core_service import CoreService
from src.services.web_service import WebService
from src.lib.utils.session_manager import SessionManager, WebSessionManager
from src.lib import global_vars
from dotenv import load_dotenv
from os import getenv
import argparse

load_dotenv()


def init():
    parser = argparse.ArgumentParser(
        description="A python-based timesheet/childcare solution with an integrated REST api server "
                    "built for Providence Christian Academy. Developed by Elwis Salinas, Jason Jerome, Elleni Adhanom, "
                    "Robert Gryder, Ramisa Resha, and Dimitrik Johnson as members of Team Delta at George Mason University."
    )
    parser._action_groups.pop()
    optional_args = parser.add_argument_group("Optional Arguments")

    # Launch parameters
    optional_args.add_argument('--host', dest='server_ip', required=False, default=getenv('MARIADB_HOST'),
                               help='Enter the mariadb server IP using this parameter if a .env file is not present.')
    optional_args.add_argument('--port', dest='server_port', required=False, default=getenv('MARIADB_PORT'),
                               help='Enter the mariadb server port using this parameter if a .env file is not present.')
    optional_args.add_argument('--user', dest='user', required=False, default=getenv('MARIADB_USER'),
                               help='Enter the username of the mariadb account if a .env file is not present.')
    optional_args.add_argument('--pass', dest='password', required=False, default=getenv('MARIADB_PASS'),
                               help='Enter the password of the mariadb account if a .env file is not present.')
    optional_args.add_argument('--database', dest='db_name', required=False, default=getenv('MARIADB_DATABASE'),
                               help='Enter the name of the mariadb database if a .env file is not present.')
    optional_args.add_argument('--web_host', dest='web_ip', required=False, default=getenv('WEB_HOST'),
                               help='Enter the web server IP if a .env file is not present.')
    optional_args.add_argument('--web_port', dest='web_port', required=False, default=getenv('WEB_PORT'),
                               help='Enter the desired REST server port if a .env file is not present.')
    optional_args.add_argument('--debug', dest='debug_mode', action='store_true', required=False, default=False,
                               help='Enter the name of the mariadb database if a .env file is not present.')

    args = parser.parse_args()

    if args.debug_mode:
        global_vars.debug_mode = True

    try:
        session_manager = SessionManager(args.server_ip, args.server_port, args.db_name,
                                         args.user, args.password, global_vars.debug_mode)
        web_session_manager = WebSessionManager(args.web_ip, args.web_port, global_vars.debug_mode)
        CoreService(session_manager, web_session_manager)
    except RuntimeError as e:
        from sys import exit
        print(f"Encountered a fatal error!\n{e}")
        exit(-1)


if __name__ == "__main__":
    init()
