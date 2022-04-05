import uuid
from datetime import datetime, timedelta
from fastapi import HTTPException, status

from server.lib.data_classes.employee_contact_info import EmployeeContactInfo
from server.lib.utils.email_utils import send_email
from server.lib.utils.employee_utils import create_employee_password_hashes
from server.lib.config_manager import ConfigManager
from server.lib.data_classes.reset_token import ResetToken
from server.lib.database_manager import get_db_session
from server.lib.data_classes.employee import Employee, PydanticForgotPassword, PydanticResetPassword
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import sql


async def generate_code():
    return str(uuid.uuid4()).upper()[:8]


async def generate_reset_code(forgot_password: PydanticForgotPassword, session: Session = None):
    if session is None:
        session = next(get_db_session())
    if forgot_password.employee_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The reset code cannot be generated if the employee ID is null!")
    employee_id = forgot_password.employee_id.strip().lower()
    employee = session.query(Employee).filter(
        Employee.EmployeeID == employee_id
    ).first()
    if employee is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot find an employee with a matching employee ID!")
    reset_code = await generate_code()
    if reset_code is None:
        raise RuntimeError(f"Unable to generate a reset code for the following employee: {employee_id}")
    else:
        reset_token = session.query(ResetToken).filter(
            ResetToken.EmployeeID == employee_id
        ).first()
        code_issue = int((datetime.utcnow()).timestamp())
        code_expiration = int((datetime.utcnow() + timedelta(minutes=int(ConfigManager().config()['Security Settings']['reset_code_expiry_minutes']))).timestamp())
        if reset_token:
            reset_token.ResetToken = reset_code
            reset_token.Iss = code_issue
            reset_token.Exp = code_expiration
            reset_token.EntryCreated = sql.func.now()
        else:
            try:
                reset_token = ResetToken(
                    token=reset_code,
                    employee_id=employee_id,
                    iss=code_issue,
                    exp=code_expiration
                )
                session.add(reset_token)
                session.flush()
            except IntegrityError:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot find an employee with a matching employee ID!")
    session.commit()
    # Send notification to the primary email that the account has requested a password reset.
    if employee.EmployeeContactInfo.PrimaryEmail:
        send_email(
            to_user=f'{employee.FirstName} {employee.LastName}',
            to_email=employee.EmployeeContactInfo.PrimaryEmail,
            subj="Account Password Reset Code",
            messages=["Your employee account's password reset code is provided below:",
                      f"<b>Reset Code: {reset_code}</b>",
                      "<b>This reset code is temporary and expires in 24 hours.</b>",
                      "Please enter this unique code in the password reset form accessible from the login page.",
                      f"If you don't remember sending a request to reset your password, or are not aware of an administrator doing so on your behalf, "
                      f"please contact an administrator as soon as possible!"]
        )
    return reset_token


async def reset_account_password(reset_password: PydanticResetPassword, session: Session = None):
    if session is None:
        session = next(get_db_session())
    if None in (reset_password.reset_code, reset_password.new_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A reset code and new password must be provided to reset an employee account's password.")

    reset_password.reset_code = reset_password.reset_code.strip()
    reset_password.new_password = reset_password.new_password.strip()
    try:
        matching_employee = session.query(Employee, ResetToken).filter(
            ResetToken.EmployeeID == Employee.EmployeeID,
            ResetToken.ResetToken == reset_password.reset_code
        ).first()
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot find an employee with a matching employee ID!")
    if matching_employee is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The reset code provided is invalid! Please try sending a new reset request.")

    employee = matching_employee[0]
    reset_token = matching_employee[1]

    cur_time = int(datetime.utcnow().timestamp())
    if reset_token.Exp <= cur_time:
        session.delete(reset_token)
        session.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The provided reset code has expired! Please try sending a new reset request.")
    else:
        password_hash = await create_employee_password_hashes(reset_password.new_password)
        if password_hash is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The plain text password provided to is invalid!")
        employee.PasswordHash = password_hash
        session.delete(reset_token)
    session.commit()
    # Send notification to the primary email that the account has had a password update.
    if employee.EmployeeContactInfo.PrimaryEmail:
        send_email(
            to_user=f'{employee.FirstName} {employee.LastName}',
            to_email=employee.EmployeeContactInfo.PrimaryEmail,
            subj="Account Password Reset Confirmed",
            messages=["<b>Your employee account's password has been reset!</b>",
                      f"If you don't remember resetting your employee account's password, please contact administration as soon as possible!"]
        )
    return employee
