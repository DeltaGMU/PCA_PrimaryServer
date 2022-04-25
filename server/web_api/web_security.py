"""
This module contains utility methods to handle web security functionality for the API server.
This includes generating access tokens, blacklisting tokens, etc.
"""

from __future__ import annotations
import traceback
import jwt
from typing import List, Dict
from datetime import timedelta, datetime
from fastapi import HTTPException, status
from fastapi.security.oauth2 import OAuth2PasswordBearer
from jwt.exceptions import PyJWTError
from server.lib.config_manager import ConfigManager
from server.lib.logging_manager import LoggingManager
from server.lib.strings import LOG_ORIGIN_AUTH, LOG_WARNING_AUTH
from server.lib.data_models.employee import Employee
from server.lib.data_models.access_token import TokenBlacklist
from server.lib.database_controllers.employee_interface import get_employee, get_employee_security_scopes
from server.lib.database_manager import get_db_session
from sqlalchemy.exc import IntegrityError

oauth_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


async def create_access_token(employee_user: Employee) -> Dict[str, str]:
    """
    A utility method used to generate an access token for an employee account upon successful sign-in.
    This method generates a JSON Web Token (JWT) with the current time as the issue time,
    expiration time as specified in the server configuration file, and includes the appropriate
    security scopes for the signed-in employee account.

    :param employee_user: The employee record associated to the account that signed-in to the server.
    :type employee_user: Employee, required
    :return: A JSON-Compatible dictionary containing basic employee account information and access token information.
    :rtype: Dict[str, str]
    """
    if employee_user is None:
        raise RuntimeError('An access token cannot be created for a null user!')
    token_issue = int((datetime.utcnow()).timestamp())
    token_expiration = int((datetime.utcnow() + timedelta(minutes=int(ConfigManager().config()['Security Settings']['access_token_expiry_minutes']))).timestamp())
    token_scopes = await get_employee_security_scopes(employee_user)
    token_data = {
        "sub": employee_user.EmployeeID,
        "iat": token_issue,
        "exp": token_expiration,
        "scopes": token_scopes
    }
    jwt_token = jwt.encode(token_data, ConfigManager().config()['API Server']['server_secret'], algorithm="HS256")
    return {"employee_id": employee_user.EmployeeID, "first_name": employee_user.FirstName, "token": jwt_token, "token_type": 'Bearer', "iat": token_issue, "exp": token_expiration}


async def get_user_from_token(token: str, session=None) -> Employee | None:
    """
    This utility method decodes a JSON Web Token (JWT) to retrieve the employee account ID.
    Using this ID, the employee record is retrieved from the database and returned.

    :param token: The access token of the employee account.
    :type token: str, required
    :param session: The database session used to retrieve the employee record.
    :type session: Session, optional
    :return: None if there is a JWT decode error, otherwise the employee record associated with the employee ID decoded from the JWT.
    :rtype: Employee | None
    """
    try:
        decoded_token = jwt.decode(token, ConfigManager().config()['API Server']['server_secret'], algorithms=["HS256"])
    except PyJWTError:
        return None
    employee_user = await get_employee(decoded_token['sub'], session)
    return employee_user


async def token_is_valid(token: str, scopes: List[str]) -> bool:
    """
    This utility method verifies the validity of a user access token and ensures
    that the permissions scopes match those of the employee account.
    This utility method is used frequently for protected API routes to ensure
    only authenticated users can access the endpoints.

    :param token: The access token of the employee account that needs to be verified.
    :type token: str, required
    :param scopes: A list of the permission scopes that the employee account must possess to be verified.
    :type scopes: List[str]
    :return: True if the access token corresponding to the employee account is valid and contains the correct permission scopes.
    :rtype: bool
    :raises HTTPException: If the access token is invalid or expired, or the employee account doesn't have the appropriate permission scopes.
    """
    if None in (token, scopes):
        return False
    try:
        token_data = jwt.decode(token, ConfigManager().config()['API Server']['server_secret'], algorithms=["HS256"])
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


async def add_token_to_blacklist(token: str) -> bool:
    """
    This utility method adds the provided access token to the access token blacklist.
    This is to prevent JWT hijacking so access tokens are blacklisted when they expire or the user account signs out.

    :param token: The access token of the employee account that needs to be blacklisted.
    :type token: str, required
    :return: True if the access token was successfully blacklisted.
    :rtype: bool
    :raises HTTPException: If the access token is invalid or expired, or the token has already been invalidated and blacklisted.
    """
    try:
        token_data = jwt.decode(token, ConfigManager().config()['API Server']['server_secret'], algorithms=["HS256"])
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
