from server.lib.strings import ROOT_DIR
from os import path, makedirs, unlink


def create_reports_directory():
    if not path.exists(f"{ROOT_DIR}/reports"):
        makedirs(f"{ROOT_DIR}/reports")
    if not path.exists(f"{ROOT_DIR}/reports/employees"):
        makedirs(f"{ROOT_DIR}/reports/employees")
    if not path.exists(f"{ROOT_DIR}/reports/students"):
        makedirs(f"{ROOT_DIR}/reports/students")


def delete_time_sheet_report(file_name) -> bool:
    if path.exists(f"{ROOT_DIR}/reports/employees/{file_name}"):
        unlink(f"{ROOT_DIR}/reports/employees/{file_name}")
        return True
    return False


def delete_care_report(file_name) -> bool:
    if path.exists(f"{ROOT_DIR}/reports/students/{file_name}"):
        unlink(f"{ROOT_DIR}/reports/students/{file_name}")
        return True
    return False
