from __future__ import annotations
import traceback
import jwt
from datetime import timedelta, datetime
from fastapi.security.oauth2 import OAuth2PasswordBearer
from jwt.exceptions import PyJWTError
from config import ENV_SETTINGS
from lib.logging_manager import LoggingManager
from lib.strings import LOG_ORIGIN_AUTH, LOG_WARNING_AUTH
from server.lib.data_classes.employee import Employee
from server.lib.data_classes.access_token import TokenBlacklist
from server.lib.database_access.employee_interface import get_employee_role, get_employee
# from server.lib.token_manager import get_blacklist_session
from server.lib.database_manager import get_db_session
from server.web_api.security_config import TOKEN_EXPIRY_MINUTES
from sqlalchemy.exc import IntegrityError

oauth_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


async def create_access_token(employee_user: Employee):
    if employee_user is None:
        raise RuntimeError('An access token cannot be created for a null user!')
    token_issue = int((datetime.utcnow()).timestamp())
    token_expiration = int((datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRY_MINUTES)).timestamp())
    token_data = {
        "sub": employee_user.EmployeeID,
        "iat": token_issue,
        "exp": token_expiration,
        "scopes": [(await get_employee_role(employee_user)).Name]
    }
    jwt_token = jwt.encode(token_data, ENV_SETTINGS.server_secret, algorithm="HS256")
    return {"first_name": employee_user.FirstName, "token": jwt_token, "token_type": 'Bearer', "iat": token_issue, "exp": token_expiration}


async def get_user_from_token(token: str, session = None):
    if await token_is_valid(token):
        try:
            decoded_token = jwt.decode(token, ENV_SETTINGS.server_secret, algorithms=["HS256"])
        except PyJWTError:
            return None
        employee_user = await get_employee(decoded_token['sub'], session)
        return employee_user
    return None


async def token_is_valid(token: str) -> bool:
    if token is None:
        return False
    try:
        jwt.decode(token, ENV_SETTINGS.server_secret, algorithms=["HS256"])
    except PyJWTError:
        return False

    # Remove expired tokens before checking validity.
    cur_time = int(datetime.utcnow().timestamp())
    session = next(get_db_session())
    session.query(TokenBlacklist).filter(
        TokenBlacklist.token == token,
        TokenBlacklist.exp <= cur_time
    ).delete()
    session.commit()

    blacklist_token = session.query(TokenBlacklist).filter(
        TokenBlacklist.token == token
    ).first()
    if blacklist_token:
        return False
    return True


async def add_token_to_blacklist(token: str) -> bool | None:
    if not await token_is_valid(token):
        return False
    try:
        decoded_token = jwt.decode(token, ENV_SETTINGS.server_secret, algorithms=["HS256"])
    except PyJWTError:
        return None
    # token_db[token] = decoded_token['exp']
    blacklist_token = TokenBlacklist(token, decoded_token['iat'], decoded_token['exp'])
    try:
        session = next(get_db_session())
        session.add(blacklist_token)
        session.commit()
        LoggingManager().log(LoggingManager.LogLevel.LOG_INFO, "A user has logged out and the authentication token has been invalidated and blacklisted.", origin=LOG_ORIGIN_AUTH, no_print=False)
    except IntegrityError:
        LoggingManager().log(LoggingManager.LogLevel.LOG_WARNING, "Runtime Warning: The token to blacklist has already been added to the database, so it will be ignored.", origin=LOG_ORIGIN_AUTH, error_type=LOG_WARNING_AUTH,
                             exc_message=traceback.format_exc(), no_print=False)
        return True
    return True
