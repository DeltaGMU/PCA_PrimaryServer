from fastapi import Body, status, HTTPException, Depends, Security
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from config import ENV_SETTINGS
from server.lib.utils.email_utils import send_test_email
from server.web_api.models import ResponseModel
from server.lib.data_classes.employee import Employee, PydanticEmployeeRegistration, PydanticEmployeesRemoval, PydanticEmployeeUpdate, \
    PydanticRetrieveMultipleEmployees, PydanticMultipleEmployeesUpdate
from server.lib.database_manager import get_db_session
from server.lib.database_access.employee_interface import get_employee_role, get_employee_contact_info, get_all_employees, get_employee, \
    create_employee, remove_employees, update_employee, get_multiple_employees, update_employees, is_admin
from server.web_api.web_security import token_is_valid, oauth_scheme, get_user_from_token

router = InferringRouter()


# pylint: disable=R0201
@cbv(router)
class EmailRouter:
    class Create:
        @staticmethod
        @router.post(ENV_SETTINGS.API_ROUTES.Email.send_test_email, status_code=status.HTTP_200_OK)
        async def test_email(token: str = Depends(oauth_scheme)):
            if not await token_is_valid(token, ["administrator"]):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired or is invalid!")
            json_resp = send_test_email()
            return ResponseModel(status.HTTP_201_CREATED, "success", json_resp)
