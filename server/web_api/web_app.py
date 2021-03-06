from fastapi.exceptions import RequestValidationError

from server.lib.config_manager import ConfigManager
from server.web_api.models import ResponseModel
from server.web_api.routing.v1 import core_routing, employee_routing, employee_hours_routing, student_routing, \
    student_care_routing, reports_routing, email_routing, student_grade_routing
from server.web_api.web_security import add_token_to_blacklist, create_access_token, get_user_from_token, oauth_scheme, token_is_valid
from server.lib.database_controllers.employee_interface import get_employee
from fastapi import FastAPI, Depends, status, HTTPException, Request
from starlette.middleware.cors import CORSMiddleware
from pydantic import ValidationError
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from server.web_api.api_routes import API_ROUTES
from server.lib.utils.employee_utils import verify_employee_password
from server.lib.strings import META_VERSION, ROOT_DIR
from starlette.exceptions import HTTPException as StarletteHTTPException

web_app = FastAPI(
    title="PCA Web API",
    description="This is the REST API for the PCA Timesheet & Student Care Service server built with FastAPI",
    version=META_VERSION,
    redoc_url=None
)
web_app.add_middleware(
    CORSMiddleware,
    allow_origins=[f"{'https' if ConfigManager().config().getboolean('API Server', 'use_https') else 'http'}://{cors_domain.strip()}" for cors_domain in ConfigManager().config()['API Server']['cors_domains'].lower().strip().split(",")],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Origin", "Accept", "Content-Type", "Authorization", "Access-Control-Allow-Origin"]
)
if ConfigManager().config().getboolean('API Server', 'use_https'):
    from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

    web_app.add_middleware(HTTPSRedirectMiddleware)
if ConfigManager().config().getboolean('API Server', 'enable_docs'):
    web_app.mount("/wiki",
                  StaticFiles(directory=f"{ROOT_DIR}/docs/build/html", html=True),
                  name="wiki")
web_app.mount("/favicon.ico", FileResponse(f"{ROOT_DIR}/web_api/static/favicon.ico"))
web_app.include_router(core_routing.router)
web_app.include_router(employee_routing.router)
web_app.include_router(employee_hours_routing.router)
web_app.include_router(student_routing.router)
web_app.include_router(student_care_routing.router)
web_app.include_router(student_grade_routing.router)
web_app.include_router(reports_routing.router)
web_app.include_router(email_routing.router)


@web_app.get(API_ROUTES.index, status_code=status.HTTP_200_OK)
async def serve_index():
    """
    Serves the index page of the uvicorn API server with the original request sent to the server.

    :return: The index page of the uvicorn API server.
    :rtype: server.web_api.models.ResponseModel
    """
    return ResponseModel(status.HTTP_200_OK, "success", {"message": {}})


@web_app.post(API_ROUTES.login, status_code=status.HTTP_200_OK)
async def login(data: OAuth2PasswordRequestForm = Depends()):
    """
    An endpoint to handle login requests to the server which verifies employee accounts before allowing access.

    :param data: The username and password of the employee account.
    :type data: OAuth2PasswordRequestForm
    :return: A response model containing basic employee account information and access token information.
    :rtype: server.web_api.models.ResponseModel
    :raises HTTPException: If the username or password is invalid, the employee account is disabled, or a network connection cannot be established.
    """
    username = data.username.strip()
    password = data.password.strip()

    employee_user = await get_employee(username)
    if employee_user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid username or password provided!")
    else:
        employee_verified = await verify_employee_password(password, employee_user.PasswordHash)
        if employee_verified is None or employee_verified is False:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid username or password provided!")
    if not employee_user.EmployeeEnabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The user account is currently disabled. Please inform your system administrator.")
    access_token_dict = await create_access_token(employee_user)
    return ResponseModel(status.HTTP_200_OK, "success", {**access_token_dict})


@web_app.get(API_ROUTES.me, status_code=status.HTTP_200_OK)
async def logged_in_welcome(token: str = Depends(oauth_scheme)):
    """
    An endpoint to welcome a signed-in account and return the first and last name information
    from the employee account.

    :param token: The access token of the signed-in user.
    :type token: str, required
    :return: A response model containing a success message and the first and last name of the signed in account.
    :rtype: server.web_api.models.ResponseModel
    :raises HTTPException: If the user access token has expired or is invalid.
    """
    if not await token_is_valid(token, ["employee"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired or is invalid!")
    user = await get_user_from_token(token, )
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is invalid or expired!")
    return ResponseModel(status.HTTP_200_OK, "logged in successfully!", {"user": f"{user.FirstName} {user.LastName}".title()})


@web_app.post(API_ROUTES.logout, status_code=status.HTTP_200_OK)
async def logout(token: str = Depends(oauth_scheme)):
    """
    An endpoint that logs out a signed-in employee account and invalidates and blacklists the access token to prevent
    JWT hijacking.

    :param token: The access token of the signed-in user.
    :type token: str, required
    :return: A response model containing a success message.
    :rtype: server.web_api.models.ResponseModel
    :raises HTTPException: If the user access token has expired or is invalid.
    """
    token_blacklist_check = await add_token_to_blacklist(token)
    if token_blacklist_check is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token is invalid or expired!")
    elif not token_blacklist_check:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token already invalidated!")
    return ResponseModel(status.HTTP_200_OK, "logged out successfully!")


@web_app.get(API_ROUTES.routes, status_code=status.HTTP_200_OK)
async def get_api_routes(token: str = Depends(oauth_scheme)):
    """
    An endpoint that retrieves all the API routes registered in the API server.
    This is a useful endpoint to verify if API routes are successfully loaded in and online.

    :param token: The access token of the signed-in user.
    :type token: str, required
    :return: A response model containing a success message and the list of all active API routes.
    :rtype: server.web_api.models.ResponseModel
    :raises HTTPException: If the user access token has expired or is invalid.
    """
    if not await token_is_valid(token, ["administrator"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired or is invalid!")
    routes_list = [{"path": route.path, "name": route.name} for route in web_app.routes]
    return ResponseModel(status.HTTP_200_OK, "routes retrieved successfully!", {"routes": routes_list})


@web_app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    The general exception handler that catches server errors from HTTP requests not caught by
    other specific exception handlers. This is called automatically when an error
    occurs on the server as a result of a request sent to the server.
    This exception handler should never be called manually in your code.

    :param request: The HTTP request that failed and resulted in an error.
    :type request: fastapi.Request
    :param exc: The exception that occurred as a result of processing the HTTP request.
    :type exc: Exception
    :return: A JSON message containing the error code, error message, and a detailed exception description.
    :rtype: fastapi.responses.JSONResponse
    """
    resp = ResponseModel(status.HTTP_500_INTERNAL_SERVER_ERROR, "Error: Internal Server Error",
                         {"error_message": f"Failed to execute: {request.method}: {request.url}",
                          "detail_message": str(exc)})
    return JSONResponse(resp.as_dict(), media_type="application/json", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@web_app.exception_handler(HTTPException)
async def general_http_exception(request: Request, exc: HTTPException):
    """
    The general exception handler that catches all HTTP errors from
    HTTP requests as a result of improper formatting or data provided in the request.
    This exception handler should never be called manually in your code.

    :param request: The HTTP request that failed and resulted in an error.
    :type request: fastapi.Request
    :param exc: The exception that occurred as a result of processing the HTTP request.
    :type exc: fastapi.HTTPException
    :return: A JSON message containing the error code, error message, and a detailed exception description.
    :rtype: fastapi.responses.JSONResponse
    """
    detail_error_message = str(exc.detail)
    if exc.status_code == 404:
        return RedirectResponse(API_ROUTES.index)
    if exc.status_code == 405:
        detail_error_message = "The request to the endpoint is invalid. This endpoint does not exist or is not allowed!"
    resp = ResponseModel(exc.status_code, "Error: HTTP Exception Error",
                         {"error_message": f"Failed to execute: {request.method}: {request.url}",
                          "detail_message": detail_error_message})
    return JSONResponse(resp.as_dict(), media_type="application/json", status_code=exc.status_code)


@web_app.exception_handler(StarletteHTTPException)
async def starlette_http_exception(request: Request, exc: StarletteHTTPException):
    """
    The general exception handler that catches HTTP errors from the uvicorn server.
    If for some reason this exception handler is caught instead of the primary exception handler for all HTTP exceptions,
    then this handler will redirect the exception to the appropriate handler.
    This exception handler should never be called manually in your code.

    :param request: The HTTP request that failed and resulted in an error.
    :type request: fastapi.Request
    :param exc: The exception that occurred as a result of processing the HTTP request.
    :type exc: starlette.exceptions.HTTPException
    :return: A JSON message containing the error code, error message, and a detailed exception description.
    :rtype: fastapi.responses.JSONResponse
    """
    return await general_http_exception(request, exc)


@web_app.exception_handler(ValidationError)
async def general_validation_exception(request: Request, exc: ValidationError):
    """
    The general exception handler that catches validation errors with data sent
    to the server in an HTTP request. This exception is caused by the HTTP request
    sent to the server and is the fault of the requester, not the server.

    :param request: HTTP request that failed and resulted in an error.
    :type request: fastapi.Request
    :param exc: The exception that occurred as a result of processing the HTTP request.
    :type exc: fastapi.exceptions.ValidationError
    :return: A JSON message containing the error code, error message, and a detailed exception description.
    :rtype: fastapi.responses.JSONResponse
    """
    resp = ResponseModel(status.HTTP_400_BAD_REQUEST, "Error: Validation Error",
                         {"error_message": f"Failed to execute: {request.method}: {request.url}",
                          "detail_message": str(exc)})
    return JSONResponse(resp.as_dict(), media_type="application/json", status_code=status.HTTP_400_BAD_REQUEST)


@web_app.exception_handler(RequestValidationError)
async def general_request_validation_exception(request: Request, exc: RequestValidationError):
    """
    The general exception handler that catches validation errors with improper formatting of requests
    sent to the server. This exception is caused by the HTTP request
    sent to the server and is the fault of the requester, not the server.

    :param request: HTTP request that failed and resulted in an error.
    :type request: fastapi.Request
    :param exc: The exception that occurred as a result of processing the HTTP request.
    :type exc: fastapi.exceptions.RequestValidationError
    :return: A JSON message containing the error code, error message, and a detailed exception description.
    :rtype: fastapi.responses.JSONResponse
    """
    resp = ResponseModel(status.HTTP_400_BAD_REQUEST, "Error: Request Validation Error",
                         {"error_message": f"Failed to execute: {request.method}: {request.url}",
                          "detail_message": str(exc)})
    return JSONResponse(resp.as_dict(), media_type="application/json", status_code=status.HTTP_400_BAD_REQUEST)
