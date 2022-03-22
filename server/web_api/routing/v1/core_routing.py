from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from config import ENV_SETTINGS
from server.web_api.models import ResponseModel
from server.lib.database_manager import is_active
from fastapi import status


router = InferringRouter()


# pylint: disable=R0201
@cbv(router)
class CoreRouter:
    @router.get(ENV_SETTINGS.API_ROUTES.core, status_code=status.HTTP_200_OK)
    def main_api(self):
        """
        An endpoint that checks the status of the v1 segment of the API service.

        :return: A response model containing the online status of the v1 segment of the API service.
        :rtype: server.web_api.models.ResponseModel
        """
        return ResponseModel(status.HTTP_200_OK, "success")

    @router.get(ENV_SETTINGS.API_ROUTES.status, status_code=status.HTTP_200_OK)
    def status(self):
        """
        An endpoint that checks the status of the database connection in the server.

        :return: A response model containing the online status of the database connection.
        :rtype: server.web_api.models.ResponseModel
        """
        return ResponseModel(status.HTTP_200_OK, "success", {"status": "online" if is_active() else "offline"})

    @router.get(f"{ENV_SETTINGS.API_ROUTES.letsencrypt}{ENV_SETTINGS.lets_encrypt_verification_route}", status_code=status.HTTP_200_OK)
    def status(self):
        return f"{ENV_SETTINGS.lets_encrypt_verification_route}.-{ENV_SETTINGS.lets_encrypt_token}"
