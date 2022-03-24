import requests
from config import ENV_SETTINGS


def send_test_email():
    # Authenticate self first...
    auth_request = requests.post(f"{ENV_SETTINGS.pca_email_api}{ENV_SETTINGS.THIRD_PARTY_ROUTES.Email.login}", data={
        "username": ENV_SETTINGS.pca_email_username.strip(),
        "password": ENV_SETTINGS.pca_email_password.strip()
    })
    resp_json = auth_request.json()
    access_token = resp_json['accessToken']

    headers = {'Authorization': f'Bearer {access_token}'}
    email_request = requests.post(f"{ENV_SETTINGS.pca_email_api}{ENV_SETTINGS.THIRD_PARTY_ROUTES.Email.send_email}", data={
        "from": ENV_SETTINGS.pca_email_username.strip(),
        "to": ENV_SETTINGS.pca_email_username.strip(),
        "subject": "self test email - please ignore!",
        "messagePlainText": "self test email - please ignore!"
    }, headers=headers)
    return email_request.json()