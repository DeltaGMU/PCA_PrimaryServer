from os import path, makedirs, unlink
from server.lib.config_manager import ConfigManager


def create_reports_directory():
    if not path.exists(f"{ConfigManager().config()['System Settings']['reports_directory']}"):
        makedirs(f"{ConfigManager().config()['System Settings']['reports_directory']}")
    if not path.exists(f"{ConfigManager().config()['System Settings']['reports_directory']}/employees"):
        makedirs(f"{ConfigManager().config()['System Settings']['reports_directory']}/employees")
    if not path.exists(f"{ConfigManager().config()['System Settings']['reports_directory']}/students"):
        makedirs(f"{ConfigManager().config()['System Settings']['reports_directory']}/students")


def delete_time_sheet_report(file_name) -> bool:
    if path.exists(f"{ConfigManager().config()['System Settings']['reports_directory']}/employees/{file_name}"):
        unlink(f"{ConfigManager().config()['System Settings']['reports_directory']}/employees/{file_name}")
        return True
    return False


def delete_care_report(file_name) -> bool:
    if path.exists(f"{ConfigManager().config()['System Settings']['reports_directory']}/students/{file_name}"):
        unlink(f"{ConfigManager().config()['System Settings']['reports_directory']}/students/{file_name}")
        return True
    return False
