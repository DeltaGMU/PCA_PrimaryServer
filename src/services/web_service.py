import threading
import uvicorn
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException
from pathlib import Path
from os import path
from src.lib.strings import META_VERSION
from src.web_api.models import ResponseModel
from src.web_api.routing.core import routing as core_routing
from src.web_api.routing.v1.employees import routing as employees_routing
from src.lib import global_vars
from src.lib.error_codes import ERR_WEB_SRVCE_NOT_INITIALIZED

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
    directory=f"{Path(path.dirname(__file__)).parent.parent}/src/web_api/static"),
    name="static")
web_app.include_router(core_routing.router)
web_app.include_router(employees_routing.router)


@web_app.exception_handler(Exception)
def general_exception_handler(request: Request, exc: Exception):
    resp = ResponseModel(400, "Error - Bad Request",
                         {"error_message": f"Failed to execute: {request.method}: {request.url}",
                          "detail_message": str(exc)})
    return JSONResponse(resp.as_dict(), media_type="application/json", status_code=400)


@web_app.exception_handler(RequestValidationError)
def general_exception_handler(request: Request, exc: Exception):
    resp = ResponseModel(422, "Error - Unprocessable Entity",
                         {"error_message": f"The provided entity was missing one or more fields!",
                          "detail_message": str(exc)})
    return JSONResponse(resp.as_dict(), media_type="application/json", status_code=400)


@web_app.exception_handler(StarletteHTTPException)
async def starlette_http_exception(request: Request, exc: Exception):
    resp = ResponseModel(404, "Error - Not Found", {"error_message": "This path is invalid!", "detail_message": str(exc)})
    return JSONResponse(resp.as_dict(), media_type="application/json", status_code=404)


@web_app.get("/")
async def serve_app(request: Request):
    return Jinja2Templates(directory=f"{Path(path.dirname(__file__)).parent.parent}/src/web_api/static/templates").TemplateResponse("index.html", {"request": request})


@web_app.get("/favicon.ico")
async def serve_favicon(request: Request):
    favicon = open(f"{Path(path.dirname(__file__)).parent.parent}/src/web_api/static/favicon.ico", mode="rb")
    return StreamingResponse(favicon, media_type="image/x-icon")


class UvicornServer(uvicorn.Server):
    def __init__(self, *args, **kwargs):
        super(UvicornServer, self).__init__(*args, **kwargs)


class ServerThreadWorker(threading.Thread):
    def __init__(self, *args, **kwargs):
        super(ServerThreadWorker, self).__init__(*args, **kwargs)
        self._stop_event = threading.Event()
        self.ip = kwargs["kwargs"]["ip"]
        self.port = int(kwargs["kwargs"]["port"])
        self.server = UvicornServer(
            config=uvicorn.Config(
                web_app,
                host=self.ip,
                port=self.port,
                reload=False,
                log_level=global_vars.logging_mode if global_vars.logging_mode else "critical",
                loop="asyncio",
                ssl_certfile=kwargs["kwargs"].get("ssl_cert"),
                ssl_keyfile=kwargs["kwargs"].get("ssl_key"),
                timeout_keep_alive=99999,
                debug=True
            )
        )

    def run(self):
        self.server.run()

    def stop(self):
        self.server.should_exit = True


class WebService:
    def __init__(self, web_session_manager, ip, port, use_https=False, ssl_cert=None, ssl_key=None):
        global_vars.web_manager = web_session_manager
        global_vars.web_manager.web_service = self
        self.web_server = ServerThreadWorker(
            kwargs={
                "ip": ip, "port": port,
                "ssl_cert": ssl_cert if use_https else None,
                "ssl_key": ssl_key if use_https else None
                },
            daemon=True
        )
        if not self.web_server:
            raise RuntimeError(f"Web Service Error [Error Code: {ERR_WEB_SRVCE_NOT_INITIALIZED}\n"
                               f"The web service was not initialized or encountered an error while initializing!\n"
                               f"If you are the server administrator, please refer to the software manual!")

        else:
            self.initialize_web()

    def initialize_web(self):
        self.web_server.run()
        # log(INFO, f"Initialized API Server on: {ip}:{port}/api/", origin=L_WEB_INTERFACE, print_mode=PrintMode.REG_PRINT.value)
        # log(INFO, f"Server API documentation can be found on: {ip}:{port}/docs/", origin=L_WEB_INTERFACE, print_mode=PrintMode.REG_PRINT.value)
        # log(INFO, f"Initialized Web Application on: {ip}:{port}/", origin=L_WEB_INTERFACE, print_mode=PrintMode.REG_PRINT.value)

    def stop_web(self):
        self.web_server.stop()
