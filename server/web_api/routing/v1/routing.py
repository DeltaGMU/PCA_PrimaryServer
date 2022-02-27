from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from server.web_api.models import ResponseModel
from server.lib.service_manager import SharedData
router = InferringRouter()

# pylint: disable=R0201
@cbv(router)
class CoreRouter:
    @router.get("/api/v1/")
    def main_api(self):
        return ResponseModel(200, "success").as_dict()

    @router.get("/api/v1/status")
    def status(self):
        return ResponseModel(200, "success", {"status": "online" if SharedData().Managers.get_database_manager().is_active() else "offline"}).as_dict()
