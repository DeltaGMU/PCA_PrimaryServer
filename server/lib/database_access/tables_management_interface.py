import traceback
from sqlalchemy.exc import SQLAlchemyError
from config import DefaultData, ENV_SETTINGS
from server.lib.logging_manager import LoggingManager
from server.lib.strings import LOG_ORIGIN_DATABASE, LOG_ERROR_DATABASE
from server.lib.database_manager import get_db_session, MainEngineBase
from server.lib.utils.employee_utils import create_employee_password_hashes_sync
from server.lib.data_classes.access_token import TokenBlacklist
from server.lib.data_classes.reset_token import ResetToken
from server.lib.data_classes.employee import Employee
from server.lib.data_classes.employee_role import EmployeeRole
from server.lib.data_classes.employee_contact_info import EmployeeContactInfo


def initialize_tables():
    if MainEngineBase is None:
        return

    # These look like unused imports, but the table creation process needs the reference.
    # noinspection PyUnresolvedReferences
    from server.lib.data_classes.student_grade import StudentGrade
    # noinspection PyUnresolvedReferences
    from server.lib.data_classes.student import Student
    # noinspection PyUnresolvedReferences
    from server.lib.data_classes.employee_hours import EmployeeHours
    MainEngineBase.metadata.create_all()
    LoggingManager().log(LoggingManager.LogLevel.LOG_INFO, 'Initialized database tables.', origin=LOG_ORIGIN_DATABASE, no_print=False)
    if initialize_roles():
        LoggingManager().log(LoggingManager.LogLevel.LOG_INFO, 'Initialized account roles.', origin=LOG_ORIGIN_DATABASE, no_print=False)


def clear_temporary_tables():
    if MainEngineBase is None:
        return
    session = next(get_db_session())
    try:
        cleared_blacklist_rows = session.query(TokenBlacklist).delete()
        LoggingManager().log(LoggingManager.LogLevel.LOG_INFO, f'Cleared access token blacklist table: {cleared_blacklist_rows} rows.', origin=LOG_ORIGIN_DATABASE, no_print=False)
        cleared_reset_rows = session.query(ResetToken).delete()
        LoggingManager().log(LoggingManager.LogLevel.LOG_INFO, f'Cleared reset token table: {cleared_reset_rows} rows.', origin=LOG_ORIGIN_DATABASE, no_print=False)
        session.commit()
    except SQLAlchemyError as err:
        LoggingManager().log(LoggingManager.LogLevel.LOG_INFO,
                             f'Encountered an error clearing the temporary token tables: {str(err)}',
                             exc_message=traceback.format_exc(),
                             origin=LOG_ORIGIN_DATABASE,
                             error_type=LOG_ERROR_DATABASE,
                             no_print=False)
        raise RuntimeWarning from err


def initialize_roles():
    if MainEngineBase is None:
        return
    session = next(get_db_session())
    account_roles = [role.strip() for role in ENV_SETTINGS.all_account_roles.lower().strip().split(',')]
    try:
        role_query = session.query(EmployeeRole).filter(
            EmployeeRole.Name.in_(account_roles)
        ).count()
        if len(account_roles) != role_query:
            session.query(EmployeeRole).delete()
            for role in account_roles:
                new_role = EmployeeRole(role)
                session.add(new_role)
            session.commit()
        return True
    except SQLAlchemyError as err:
        session.rollback()
        raise err


def create_default_admin_account():
    if MainEngineBase is None:
        return
    session = next(get_db_session())
    default_info = DefaultData.default_admin
    try:
        # Retrieve the Role ID for an administrator account.
        role_query = session.query(EmployeeRole).filter(EmployeeRole.Name == default_info['role']).first()
        if not role_query:
            # Check if the administrator role exists, initialize the default roles if it does not exist.
            raise RuntimeError("The provided default administrator role is invalid or does not exist in the database!")
        default_admin_role_id = role_query.id
        # Create the Contact Info record for the administrator account.
        default_admin_contact_info = EmployeeContactInfo(
            employee_id=default_info['employee_id'],
            primary_email=default_info['primary_email'],
            enable_primary_email_notifications=default_info['enable_primary_email_notifications']
        )
        # session.add(default_admin_contact_info)
        # session.flush()

        # Create the administrator account password hashes.
        default_admin_password = create_employee_password_hashes_sync(default_info['plain_password'])
        # Create the administrator account from the computed information.
        default_admin = Employee(default_info['employee_id'], default_info['first_name'], default_info['last_name'],
                                 default_admin_password, default_admin_role_id, default_admin_contact_info, enabled=True)
        session.add(default_admin)
        session.commit()
    except SQLAlchemyError as err:
        LoggingManager().log(LoggingManager.LogLevel.LOG_CRITICAL,
                             f'Encountered an error checking/setting-up the account roles: {str(err)}',
                             exc_message=traceback.format_exc(),
                             origin=LOG_ORIGIN_DATABASE,
                             error_type=LOG_ERROR_DATABASE,
                             no_print=False)
        raise err


def initialize_admin():
    if MainEngineBase is None:
        return
    session = next(get_db_session())
    try:
        # Check if there are any administrator accounts existing in the database.
        check_admin_acc = session.query(Employee, EmployeeRole).filter(
            Employee.EmployeeRoleID == EmployeeRole.id,
            EmployeeRole.Name == 'administrator'
        ).count()
        if check_admin_acc != 0:
            # Check if any of the existing administrator accounts are enabled.
            check_enabled_acc = session.query(Employee, EmployeeRole).filter(
                Employee.EmployeeRoleID == EmployeeRole.id,
                Employee.EmployeeEnabled == 1,
                EmployeeRole.Name == 'administrator'
            ).count()
            # If all existing administrator accounts are disabled, check for the default administrator account.
            if check_enabled_acc == 0:
                check_default_acc = session.query(Employee, EmployeeRole).filter(
                    Employee.EmployeeID == 'admin',
                    Employee.EmployeeRoleID == EmployeeRole.id,
                    Employee.EmployeeEnabled == 0,
                    EmployeeRole.Name == 'administrator'
                ).first()
                # If all the existing administrator accounts are disabled AND the default administrator account (if it exists) is disabled, enable it.
                if check_default_acc:
                    LoggingManager().log(LoggingManager.LogLevel.LOG_WARNING,
                                         f'No administrator accounts enabled, enabling the default administrator account... '
                                         f'Please be sure to delete this account after enabling/setting-up a new administrator account!',
                                         origin=LOG_ORIGIN_DATABASE,
                                         no_print=False)
                    check_default_acc = check_default_acc[0]
                    check_default_acc.EmployeeEnabled = True
                    session.commit()
                # If all the existing administrator accounts are disabled AND the default administrator does not exist, create it.
                else:
                    create_default_admin_account()
            else:
                LoggingManager().log(LoggingManager.LogLevel.LOG_INFO,
                                     'Detected one or more enabled administrator accounts in the database, skipping default administrator account initialization...')
        else:
            # If there are no existing administrator accounts, create and initialize the default administrator account.
            LoggingManager().log(LoggingManager.LogLevel.LOG_WARNING,
                                 f'No administrator accounts detected, creating and enabling the default administrator account... '
                                 f'Please be sure to delete this account after setting up a new administrator account!',
                                 origin=LOG_ORIGIN_DATABASE,
                                 no_print=False)
            create_default_admin_account()
    except SQLAlchemyError as err:
        session.rollback()
        LoggingManager().log(LoggingManager.LogLevel.LOG_CRITICAL,
                             f'Encountered an error checking/setting-up the default administrator account: {str(err)}',
                             exc_message=traceback.format_exc(),
                             origin=LOG_ORIGIN_DATABASE,
                             error_type=LOG_ERROR_DATABASE,
                             no_print=False)
        raise RuntimeWarning from err
