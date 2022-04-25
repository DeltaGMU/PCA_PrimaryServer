from fastapi import status
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from server.web_api.api_routes import API_ROUTES
from server.web_api.models import ResponseModel
from server.lib.database_manager import is_active


router = InferringRouter()


# pylint: disable=R0201
@cbv(router)
class CoreRouter:
    @router.get(API_ROUTES.core, status_code=status.HTTP_200_OK)
    def main_api(self):
        """
        An endpoint that checks the status of the v1 segment of the API service.

        :return: A response model containing the online status of the v1 segment of the API service.
        :rtype: server.web_api.models.ResponseModel
        """
        return ResponseModel(status.HTTP_200_OK, "success")

    @router.get(API_ROUTES.status, status_code=status.HTTP_200_OK)
    def status(self):
        """
        An endpoint that checks the status of the database connection in the server.

        :return: A response model containing the online status of the database connection.
        :rtype: server.web_api.models.ResponseModel
        """
        return ResponseModel(status.HTTP_200_OK, "success", {"status": "online" if is_active() else "offline"})
