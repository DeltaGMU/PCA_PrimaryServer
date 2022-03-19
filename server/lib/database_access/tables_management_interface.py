from sqlalchemy.exc import SQLAlchemyError
from server.lib.data_classes.employee import Employee
from server.lib.data_classes.employee_hours import EmployeeHours
from server.lib.data_classes.employee_role import EmployeeRole
from server.lib.data_classes.student import Student
from server.lib.data_classes.student_care_hours import StudentCareHours
from server.lib.data_classes.contact_info import ContactInfo
from server.lib.logging_manager import LoggingManager
from server.lib.strings import LOG_ORIGIN_DATABASE, LOG_ERROR_DATABASE
from server.lib.data_classes.access_token import TokenBlacklist
from server.lib.data_classes.reset_token import ResetToken
from server.lib.database_manager import get_db_session, MainEngineBase, main_engine


def initialize_tables():
    if MainEngineBase is None:
        return
    ResetToken.__table__.create(bind=main_engine, checkfirst=True)
    TokenBlacklist.__table__.create(bind=main_engine, checkfirst=True)
    ContactInfo.__table__.create(bind=main_engine, checkfirst=True)
    Employee.__table__.create(bind=main_engine, checkfirst=True)
    EmployeeHours.__table__.create(bind=main_engine, checkfirst=True)
    EmployeeRole.__table__.create(bind=main_engine, checkfirst=True)
    Student.__table__.create(bind=main_engine, checkfirst=True)
    StudentCareHours.__table__.create(bind=main_engine, checkfirst=True)
    LoggingManager().log(LoggingManager.LogLevel.LOG_INFO, 'Initialized database tables.', origin=LOG_ORIGIN_DATABASE, no_print=False)


def clear_temporary_tables():
    if MainEngineBase is None:
        return
    session = next(get_db_session())
    try:
        cleared_blacklist_rows = session.query(TokenBlacklist).delete()
        LoggingManager().log(LoggingManager.LogLevel.LOG_INFO, f'Cleared access token blacklist table: {cleared_blacklist_rows} rows.', origin=LOG_ORIGIN_DATABASE, no_print=False)
        cleared_reset_rows = session.query(ResetToken).delete()
        LoggingManager().log(LoggingManager.LogLevel.LOG_INFO, f'Cleared reset token table: {cleared_reset_rows} rows.', origin=LOG_ORIGIN_DATABASE, no_print=False)
    except SQLAlchemyError as err:
        LoggingManager().log(LoggingManager.LogLevel.LOG_INFO,
                             f'Encountered an error clearing the temporary token tables: {str(err)}',
                             exc_message=str(err),
                             origin=LOG_ORIGIN_DATABASE,
                             error_type=LOG_ERROR_DATABASE,
                             no_print=False)
        raise RuntimeWarning from err
