from server.lib.logging_manager import LoggingManager
from server.lib.strings import LOG_ORIGIN_STARTUP
from server.services.web_service import WebService
from server.lib.error_codes import ERR_WEB_SESSION_MNGR_INCORRECT_PARAMS
from config import ENV_SETTINGS


class WebSessionManager:
    """
    This class contains the logic to establish the built-in API server for front-end interaction.
    It contains methods to start and stop the web server.

    :param web_ip: The IP address should be used for the web server. (Example: 127.0.0.1)
    :type web_ip: str, required
    :param web_port: The port that should be used for the web server. (Example: 56709)
    :type web_port: int, required
    :raises RuntimeError: If the provided ``web_ip`` or ``web_port`` is null.
    """

    def __init__(self, web_ip: str, web_port: int):
        if None in (web_ip, web_port):
            raise RuntimeError(f"Web Session Manager Error [Error Code: {ERR_WEB_SESSION_MNGR_INCORRECT_PARAMS}]\n"
                               "One or more parameters provided to start the service was null!\n"
                               "Please check your .env file or include the missing parameters as startup arguments.\n"
                               "If you are a server administrator, please refer to the software manual!")
        self.web_ip = web_ip
        self.web_port = web_port
        self.web_service = None
        self.initialize()

    def initialize(self):
        """
        Initializes the web service with the IP address and Port provided in the class constructor.

        :return: None
        """
        # TODO: Add https/ssl certs into the service later.
        self.web_service: WebService = WebService(self.web_ip, self.web_port, debug_mode=ENV_SETTINGS.debug_mode)
        LoggingManager().log(LoggingManager.LogLevel.LOG_INFO, "Web session manager initialized.", origin=LOG_ORIGIN_STARTUP, no_print=False)

    def start_web_server(self):
        """
        Starts the web server if it has already been initialized.

        :return: None
        """
        if self.web_service:
            self.web_service.initialize_web()

    def stop_web_server(self):
        """
        Stops the actively running web server.

        :return: None
        """
        if self.web_service:
            self.web_service.stop_web()
