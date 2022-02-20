from src.lib.strings import META_NAME, META_VERSION, LOG_ORIGIN_GENERAL
from src.lib.service_manager import SharedData


def debug_print(message: str, origin: str = None, error_type: str = None):
    if SharedData().Settings.get_debug_mode():
        print(f'[{META_NAME}({META_VERSION}).{origin if origin else LOG_ORIGIN_GENERAL}]'
              f'{f"<{error_type}>:" if error_type else ""} {message}')


def console_print(message: str, origin: str = None, error_type: str = None):
    if not SharedData().Settings.get_debug_mode():
        print(f'[{META_NAME}({META_VERSION}).{origin if origin else LOG_ORIGIN_GENERAL}]'
              f'{f"<{error_type}>:" if error_type else ""} {message}')
