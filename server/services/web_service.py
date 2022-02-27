import contextlib
import threading
import time
import uvicorn
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.exceptions import RequestValidationError, ValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
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
web_app.mount("/static", StaticFiles(
    directory=f"{ROOT_DIR}/web_api/static"),
    name="static")
web_app.include_router(v1_routing.router)
web_app.include_router(employees_routing.router)
web_app.include_router(students_routing.router)


@web_app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    resp = ResponseModel(status.HTTP_500_INTERNAL_SERVER_ERROR, "Error: Internal Server Error",
                         {"error_message": f"Failed to execute: {request.method}: {request.url}",
                          "detail_message": str(exc)})
    return JSONResponse(resp.as_dict(), media_type="application/json", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@web_app.exception_handler(HTTPException)
async def general_http_exception(request: Request, exc: HTTPException):
    resp = ResponseModel(exc.status_code, "Error: HTTP Exception Error",
                         {"error_message": f"Failed to execute: {request.method}: {request.url}",
                          "detail_message": str(exc.detail)})
    return JSONResponse(resp.as_dict(), media_type="application/json", status_code=exc.status_code)


@web_app.exception_handler(ValidationError)
async def general_validation_exception(request: Request, exc: ValidationError):
    resp = ResponseModel(status.HTTP_400_BAD_REQUEST, "Error: Validation Error",
                         {"error_message": f"Failed to execute: {request.method}: {request.url}",
                          "detail_message": str(exc)})
    return JSONResponse(resp.as_dict(), media_type="application/json", status_code=status.HTTP_400_BAD_REQUEST)


@web_app.exception_handler(RequestValidationError)
async def general_request_validation_exception(request: Request, exc: RequestValidationError):
    resp = ResponseModel(status.HTTP_400_BAD_REQUEST, "Error: Request Validation Error",
                         {"error_message": f"Failed to execute: {request.method}: {request.url}",
                          "detail_message": str(exc)})
    return JSONResponse(resp.as_dict(), media_type="application/json", status_code=status.HTTP_400_BAD_REQUEST)


@web_app.get("/")
async def serve_app(request: Request):
    return Jinja2Templates(directory=f"{ROOT_DIR}/web_api/static/templates").\
        TemplateResponse("index.html", {"request": request})


@web_app.get("/favicon.ico")
async def serve_favicon():
    with open(f"{ROOT_DIR}/web_api/static/favicon.ico", mode="rb") as favicon_file:
        return StreamingResponse(favicon_file, media_type="image/x-icon")


class UvicornServer(uvicorn.Server):
    def install_signal_handlers(self) -> None:
        pass

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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
    def __init__(self, host: str, port: int, use_https: bool = False, ssl_cert: bool = None, ssl_key: bool = None, debug_mode: bool = False):
        self.host = host
        self.port = port
        self.use_https = use_https
        self.ssl_cert = ssl_cert
        self.ssl_key = ssl_key
        self.web_server = None
        self.stop_flag = False
        self.debug_mode = debug_mode

    def initialize_web(self):
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
        Sets the stop flag for the running API server thread if the web server is currently active.
        Don't attempt to call this method directly, please use the :func:`~database_manager.DatabaseManager.stop_web_server()` method instead.

        :return: None
        """
        if self.web_server:
            self.stop_flag = True
