from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from src.web_api.models import ResponseModel
from src.utils.db_utils import verify_db_active
router = InferringRouter()


@cbv(router)
class CoreRouter:
    @router.get("/api/v1/")
    async def main_api(self):
        return ResponseModel(200, "success").as_dict()

    @router.get("/api/v1/status")
    async def status(self):
        return ResponseModel(200, "success", {"status": "online" if verify_db_active() else "offline"}).as_dict()
