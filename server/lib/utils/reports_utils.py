from server.lib.strings import ROOT_DIR
from os import path, makedirs


def create_reports_directory():
    if not path.exists(f"{ROOT_DIR}/reports"):
        makedirs(f"{ROOT_DIR}/reports")
    if not path.exists(f"{ROOT_DIR}/reports/employees"):
        makedirs(f"{ROOT_DIR}/reports/employees")
    if not path.exists(f"{ROOT_DIR}/reports/students"):
        makedirs(f"{ROOT_DIR}/reports/students")

