from fastapi import status, HTTPException, Depends
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from server.web_api.api_routes import API_ROUTES
from server.lib.utils.email_utils import send_test_email
from server.web_api.models import ResponseModel
from server.web_api.web_security import token_is_valid, oauth_scheme

router = InferringRouter()


# pylint: disable=R0201
@cbv(router)
class EmailRouter:
    class Create:
        @staticmethod
        @router.post(API_ROUTES.Email.send_test_email, status_code=status.HTTP_200_OK)
        async def test_email(token: str = Depends(oauth_scheme)):
            """
            An endpoint that sends a test email from the server's SmarterMail email account to itself.
            This endpoint is useful to verify that email communications are fully functional.

            :param token: The JSON Web Token responsible for authenticating the user to this endpoint.
            :type token: str, required
            :return: A response model containing the JSON response of the test email that was sent.
            :rtype: server.web_api.models.ResponseModel
            """
            if not await token_is_valid(token, ["administrator"]):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired or is invalid!")
            json_resp = send_test_email()
            return ResponseModel(status.HTTP_200_OK, "success", json_resp)
