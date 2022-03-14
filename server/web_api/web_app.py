from fastapi.exceptions import RequestValidationError
from server.web_api.models import ResponseModel
from server.web_api.routing.v1 import core_routing, employee_routing, employee_hours_routing, student_routing
from server.web_api.web_security import add_token_to_blacklist, create_access_token, get_user_from_token, oauth_scheme, token_is_valid
from server.lib.database_access.employee_interface import get_employee
from fastapi import FastAPI, Depends, status, Security, HTTPException, Request, Response
from starlette.middleware.cors import CORSMiddleware
from pydantic import ValidationError
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from config import ENV_SETTINGS
from server.lib.utils.employee_utils import verify_employee_password
from server.lib.strings import META_VERSION, ROOT_DIR
from starlette.exceptions import HTTPException as StarletteHTTPException

web_app = FastAPI(
    title="PCA Web API",
    description="This is the REST API for the PCA server built with FastAPI",
    version=META_VERSION,
    redoc_url=None
)
web_app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://localhost"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Origin", "Accept", "Content-Type", "Authorization", "Access-Control-Allow-Origin"]
)
web_app.mount("/wiki",
              StaticFiles(directory=f"{ROOT_DIR}/docs/build/html", html=True),
              name="wiki")
web_app.mount("/favicon.ico", FileResponse(f"{ROOT_DIR}/web_api/static/favicon.ico"))
web_app.include_router(core_routing.router)
web_app.include_router(employee_routing.router)
web_app.include_router(employee_hours_routing.router)
# web_app.include_router(student_routing.router)


# Manually handle CORS preflight requests
'''
@web_app.options('/{rest_of_path:path}')
async def preflight_handler(request: Request, rest_of_path: str) -> Response:
    response = Response()
    response.headers['Access-Control-Allow-Origin'] = 'http://localhost:8080, http://localhost'
    response.headers['Access-Control-Allow-Methods'] = 'POST, GET, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Origin, Accept, Access-Control-Allow-Origin, Authorization, Content-Type'
    return response
'''


@web_app.get(ENV_SETTINGS.API_ROUTES.index, status_code=status.HTTP_200_OK)
async def serve_index():
    """
    Serves the index page of the uvicorn API server with the original request sent to the server.

    :return: The index page of the uvicorn API server.
    :rtype: fastapi.templating.Jinja2Templates
    """
    return ResponseModel(status.HTTP_200_OK, "success", {"message": {}})


@web_app.post(ENV_SETTINGS.API_ROUTES.login, status_code=status.HTTP_200_OK)
async def login(data: OAuth2PasswordRequestForm = Depends()):
    username = data.username
    password = data.password

    employee_user = await get_employee(username)
    if employee_user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid username or password provided!")
    else:
        employee_verified = await verify_employee_password(password, employee_user.PasswordHash)
        if employee_verified is None or employee_verified is False:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid username or password provided!")
    access_token_dict = await create_access_token(employee_user)
    return ResponseModel(status.HTTP_200_OK, "success", {**access_token_dict})


@web_app.get(ENV_SETTINGS.API_ROUTES.me, status_code=status.HTTP_200_OK)
async def logged_in_welcome(token: str = Depends(oauth_scheme)):
    if not await token_is_valid(token, ["teacher"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired or is invalid!")
    user = await get_user_from_token(token, )
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is invalid or expired!")
    return ResponseModel(status.HTTP_200_OK, "logged in successfully!", {"user": f"{user.FirstName} {user.LastName}"})


@web_app.post(ENV_SETTINGS.API_ROUTES.logout, status_code=status.HTTP_200_OK)
async def log_out_user(token: str = Depends(oauth_scheme)):
    token_blacklist_check = await add_token_to_blacklist(token)
    if token_blacklist_check is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token is invalid or expired!")
    elif not token_blacklist_check:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token already invalidated!")
    return ResponseModel(status.HTTP_200_OK, "logged out successfully!")


@web_app.post(ENV_SETTINGS.API_ROUTES.reset, status_code=status.HTTP_200_OK)
async def reset_password(new_password: str, reset_token: str = Depends(oauth_scheme)):
    pass


@web_app.post(ENV_SETTINGS.API_ROUTES.reset, status_code=status.HTTP_200_OK)
async def forgot_password(new_password: str, reset_token: str = Depends(oauth_scheme)):
    pass


@web_app.get(ENV_SETTINGS.API_ROUTES.routes, status_code=status.HTTP_200_OK)
async def get_api_routes(token: str = Depends(oauth_scheme)):
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
        return RedirectResponse(ENV_SETTINGS.API_ROUTES.index)
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
