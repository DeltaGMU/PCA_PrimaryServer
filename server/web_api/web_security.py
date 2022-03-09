from __future__ import annotations
import jwt
from datetime import timedelta, datetime
from fastapi.security.oauth2 import OAuth2PasswordBearer
from jwt.exceptions import PyJWTError
from config import ENV_SETTINGS
from server.lib.data_classes.employee import Employee
from server.lib.data_classes.access_token import TokenBlacklist
from server.lib.database_functions.employee_interface import get_employee_role, get_employee
# from server.lib.token_manager import get_blacklist_session
from server.lib.database_manager import get_db_session
from server.web_api.security_config import TOKEN_EXPIRY_MINUTES

oauth_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


def create_access_token(employee_user: Employee):
    if employee_user is None:
        raise RuntimeError('An access token cannot be created for a null user!')
    token_issue = int((datetime.utcnow()).timestamp())
    token_expiration = int((datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRY_MINUTES)).timestamp())
    token_data = {
        "sub": employee_user.EmployeeID,
        "iat": token_issue,
        "exp": token_expiration,
        "scopes": [get_employee_role(employee_user).Name]
    }
    jwt_token = jwt.encode(token_data, ENV_SETTINGS.server_secret, algorithm="HS256")
    return {"first_name": employee_user.FirstName, "token": jwt_token, "token_type": 'Bearer', "iat": token_issue, "exp": token_expiration}


def get_user_from_token(token: str):
    if token_is_valid(token):
        try:
            decoded_token = jwt.decode(token, ENV_SETTINGS.server_secret, algorithms=["HS256"])
        except PyJWTError:
            return None
        employee_user = get_employee(decoded_token['sub'])
        return employee_user
    return None


def token_is_valid(token: str) -> bool:
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


def add_token_to_blacklist(token: str) -> bool | None:
    if not token_is_valid(token):
        return False
    try:
        decoded_token = jwt.decode(token, ENV_SETTINGS.server_secret, algorithms=["HS256"])
    except PyJWTError:
        return None
    # token_db[token] = decoded_token['exp']
    blacklist_token = TokenBlacklist(token, decoded_token['iat'], decoded_token['exp'])
    session = next(get_db_session())
    session.add(blacklist_token)
    session.commit()
    return True
