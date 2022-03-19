from __future__ import annotations
import traceback
import jwt
from typing import List
from datetime import timedelta, datetime
from fastapi import HTTPException, status
from fastapi.security.oauth2 import OAuth2PasswordBearer
from jwt.exceptions import PyJWTError
from config import ENV_SETTINGS
from server.lib.logging_manager import LoggingManager
from server.lib.strings import LOG_ORIGIN_AUTH, LOG_WARNING_AUTH
from server.lib.data_classes.employee import Employee
from server.lib.data_classes.access_token import TokenBlacklist
from server.lib.database_access.employee_interface import get_employee, get_employee_security_scopes
from server.lib.database_manager import get_db_session
from server.web_api.security_config import TOKEN_EXPIRY_MINUTES
from sqlalchemy.exc import IntegrityError

oauth_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


async def create_access_token(employee_user: Employee):
    if employee_user is None:
        raise RuntimeError('An access token cannot be created for a null user!')
    token_issue = int((datetime.utcnow()).timestamp())
    token_expiration = int((datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRY_MINUTES)).timestamp())
    token_scopes = await get_employee_security_scopes(employee_user)
    token_data = {
        "sub": employee_user.EmployeeID,
        "iat": token_issue,
        "exp": token_expiration,
        "scopes": token_scopes
    }
    jwt_token = jwt.encode(token_data, ENV_SETTINGS.server_secret, algorithm="HS256")
    return {"employee_id": employee_user.EmployeeID, "first_name": employee_user.FirstName, "token": jwt_token, "token_type": 'Bearer', "iat": token_issue, "exp": token_expiration}


async def get_user_from_token(token: str, session=None):
    try:
        decoded_token = jwt.decode(token, ENV_SETTINGS.server_secret, algorithms=["HS256"])
    except PyJWTError:
        return None
    employee_user = await get_employee(decoded_token['sub'], session)
    return employee_user


async def token_is_valid(token: str, scopes: List[str]) -> bool:
    if None in (token, scopes):
        return False
    try:
        token_data = jwt.decode(token, ENV_SETTINGS.server_secret, algorithms=["HS256"])
        token_user = token_data.get("sub")
        if token_user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization token is missing user information!")
        token_scopes = token_data.get("scopes", [])
    except PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization token is invalid! The authorization token might be incorrectly formatted.")

    # Remove expired tokens before checking validity.
    cur_time = int(datetime.utcnow().timestamp())
    session = next(get_db_session())
    session.query(TokenBlacklist).filter(
        TokenBlacklist.Exp <= cur_time
    ).delete()
    session.commit()

    blacklist_token = session.query(TokenBlacklist).filter(
        TokenBlacklist.AccessToken == token
    ).first()
    if blacklist_token:
        return False

    for scope in scopes:
        if scope not in token_scopes:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="This user does not have enough permissions to access this content.")
    return True


async def add_token_to_blacklist(token: str) -> bool | None:
    try:
        token_data = jwt.decode(token, ENV_SETTINGS.server_secret, algorithms=["HS256"])
        token_user = token_data.get("sub")
        if token_user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization token is missing user information!")
    except PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization token is invalid! Unable to invalidate a malformed token.")

    blacklist_token = TokenBlacklist(token, token_data['iat'], token_data['exp'])
    try:
        session = next(get_db_session())
        session.add(blacklist_token)
        session.commit()
        LoggingManager().log(LoggingManager.LogLevel.LOG_INFO, "A user has logged out and the authentication token has been invalidated and blacklisted.", origin=LOG_ORIGIN_AUTH, no_print=False)
    except IntegrityError:
        LoggingManager().log(LoggingManager.LogLevel.LOG_WARNING, "Runtime Warning: The token to blacklist has already been added to the database, so it will be ignored.", origin=LOG_ORIGIN_AUTH, error_type=LOG_WARNING_AUTH,
                             exc_message=traceback.format_exc(), no_print=False)
        return False
    return True
