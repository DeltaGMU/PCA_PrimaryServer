import contextlib
import threading
import time
import uvicorn
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.exceptions import RequestValidationError, ValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException
from server.lib.logging_manager import LoggingManager
from server.lib.strings import META_VERSION, ROOT_DIR, LOG_ORIGIN_API
from server.web_api.models import ResponseModel
from server.web_api.routing.v1 import routing as v1_routing
from server.web_api.routing.v1.employees import routing as employees_routing
from server.web_api.routing.v1.students import routing as students_routing


web_app = FastAPI(
    title="PCA Web API",
    description="This is the REST API for the PCA server built with FastAPI",
    version=META_VERSION,
    redoc_url=None
)
web_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"]
)
web_app.mount("/wiki",
              StaticFiles(directory=f"{ROOT_DIR}/docs/build/html", html=True),
              name="wiki")
web_app.mount("/favicon.ico", FileResponse(f"{ROOT_DIR}/web_api/static/favicon.ico"))
web_app.include_router(v1_routing.router)
web_app.include_router(employees_routing.router)
web_app.include_router(students_routing.router)
templates = Jinja2Templates(directory=f"{ROOT_DIR}/web_api/templates")


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
        return RedirectResponse("/")
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


@web_app.get("/")
async def serve_index(request: Request):
    """
    Serves the index page of the uvicorn API server with the original request sent to the server.

    :param request: HTTP request that was sent to the server to retrieve the index page.
    :type request: fastapi.Request
    :return: The index page of the uvicorn API server.
    :rtype: fastapi.templating.Jinja2Templates
    """
    return templates.TemplateResponse("index.html", {"request": request})


class UvicornServer(uvicorn.Server):
    """
    The internal uvicorn server handler class that overrides the base uvicorn server
    configuration with updated thread handling.
    Do not modify this code!
    """
    def install_signal_handlers(self) -> None:
        pass

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.should_exit = False

    @contextlib.contextmanager
    def run_in_thread(self):
        thread = threading.Thread(target=self.run)
        thread.start()
        try:
            while not self.started:
                time.sleep(0.01)
            yield
        finally:
            self.should_exit = True
            thread.join()


class WebService:
    """
    This web service class manages the state of the web server that serves the REST API endpoints to
    the web interfaces. Please make sure that this is the last module that is initialized in the application.
    It contains methods to initialize and stop the Uvicorn web server.
    """
    def __init__(self, host: str, port: int, use_https: bool = False, ssl_cert: str = None, ssl_key: str = None, debug_mode: bool = False):
        """
        The constructor for the web service class that sets the configuration parameters
        for the uvicorn web server.

        :param host: The host IP address to use for the uvicorn server. (Example: 0.0.0.0)
        :type host: str, required
        :param port: The port to use for the uvicorn server. (Example: 56709)
        :type port: int, required
        :param use_https: Enable or disable the use of HTTPS for the uvicorn server. HTTPS is disabled by default and HTTP is used.
        :type use_https: bool, optional
        :param ssl_cert: If HTTPS is enabled, provide the SSL Certificate.
        :type ssl_cert: str, optional
        :param ssl_key: If HTTPS is enabled, provide the server's SSL Private Key.
        :type ssl_key: str, optional
        :param debug_mode: Enable or disable debug message outputs from the uvicorn server. Debug mode is disabled by default.
        :type debug_mode: bool, optional
        """
        self.host = host
        self.port = port
        self.use_https = use_https
        self.ssl_cert = ssl_cert
        self.ssl_key = ssl_key
        self.web_server = None
        self.stop_flag = False
        self.debug_mode = debug_mode

    def initialize_web(self):
        """
        Initializes the uvicorn web server for the FastAPI endpoints with the configuration parameters
        provided in the class constructor.

        :return: None
        """
        config = uvicorn.Config(
            web_app,
            host=self.host,
            port=self.port,
            reload=False,
            loop="asyncio",
            ssl_certfile=self.ssl_cert,
            ssl_keyfile=self.ssl_key,
            timeout_keep_alive=99999,
            log_level='info' if self.debug_mode else 'critical',
        )
        self.web_server = UvicornServer(config=config)
        with self.web_server.run_in_thread():
            LoggingManager().log(LoggingManager.LogLevel.LOG_INFO, f"Initializing API Server on: {self.host}:{self.port}/api/v1/", origin=LOG_ORIGIN_API, no_print=False)
            LoggingManager().log(LoggingManager.LogLevel.LOG_INFO, f"Initializing Server API Documentation on: {self.host}:{self.port}/docs/", origin=LOG_ORIGIN_API, no_print=False)
            while not self.stop_flag:
                try:
                    time.sleep(0.01)
                except KeyboardInterrupt:
                    self.stop_flag = True
            LoggingManager().log(LoggingManager.LogLevel.LOG_INFO, "Shutting down API Server.", origin=LOG_ORIGIN_API, no_print=False)
        self.stop_flag = False

    def stop_web(self):
        """
        Sets the stop flag for the running API server thread if the uvicorn web server is currently active.

        :return: None
        """
        if self.web_server:
            self.stop_flag = True
