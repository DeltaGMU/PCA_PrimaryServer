import contextlib
import threading
import time
import uvicorn
from server.web_api.web_app import web_app
from server.lib.logging_manager import LoggingManager
from server.lib.strings import LOG_ORIGIN_API


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
        except KeyboardInterrupt:
            self.should_exit = True
            thread.join()
            return
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
            ssl_certfile=self.ssl_cert if self.use_https else None,
            ssl_keyfile=self.ssl_key if self.use_https else None,
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
