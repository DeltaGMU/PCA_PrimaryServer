from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from src.web_api.models import ResponseModel
from src.lib.global_vars import SharedData
router = InferringRouter()

# pylint: disable=R0201
@cbv(router)
class CoreRouter:
    @router.get("/api/v1/")
    async def main_api(self):
        return ResponseModel(200, "success").as_dict()

    @router.get("/api/v1/status")
    async def status(self):
        return ResponseModel(200, "success", {"status": "online" if SharedData().Managers.get_session_manager().is_active() else "offline"}).as_dict()
