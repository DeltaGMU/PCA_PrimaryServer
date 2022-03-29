import re
from typing import List
import requests
from jinja2 import Environment, FileSystemLoader
from server.lib.config_manager import ConfigManager
from server.lib.strings import ROOT_DIR
from server.web_api.api_routes import THIRD_PARTY_ROUTES

email_validator_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
env = Environment(loader=FileSystemLoader(
    [
        f'{ROOT_DIR}/lib/email_service'
    ]
))


def send_test_email():
    email_api = f"{'https://' if ConfigManager().config().getboolean('Email Settings', 'pca_email_use_https') else 'http://'}{ConfigManager().config()['Email Settings']['pca_email_api']}"
    # Authenticate self first...
    auth_request = requests.post(f"{email_api}{THIRD_PARTY_ROUTES.Email.login}", data={
        "username": ConfigManager().config()['Email Settings']['pca_email_username'].strip(),
        "password": ConfigManager().config()['Email Settings']['pca_email_password'].strip()
    })
    resp_json = auth_request.json()
    access_token = resp_json['accessToken']

    # Configure authentication header...
    headers = {'Authorization': f'Bearer {access_token}'}
    # Send the email and check the response...
    email_request = requests.post(f"{email_api}{THIRD_PARTY_ROUTES.Email.send_email}", data={
        "from": ConfigManager().config()['Email Settings']['pca_email_username'].strip(),
        "to": ConfigManager().config()['Email Settings']['pca_email_username'].strip(),
        "subject": "self test email - please ignore!",
        "messagePlainText": "self test email - please ignore!"
    }, headers=headers)
    return email_request.json()


def send_email(to_user: str, to_email: List[str], subj: str, messages: List[str]):
    email_api = f"{'https://' if ConfigManager().config().getboolean('Email Settings', 'pca_email_use_https') else 'http://'}{ConfigManager().config()['Email Settings']['pca_email_api']}"
    # Validate provided information and email address.
    if None in (to_user, to_email, subj, messages):
        raise RuntimeError("Cannot send an email with the 'to', 'subject', or 'message' fields being blank!")
    if to_email and len(to_email) == 0:
        raise RuntimeError("Cannot send email to empty address(es)! Please make sure that the email address(es) is valid!")
    to = [email.lower().strip() for email in to_email]
    subj = subj.strip()
    messages = [message.strip() for message in messages]
    for email in to:
        if not re.fullmatch(email_validator_regex, email):
            raise RuntimeError("Cannot send email to invalid email address(es)! Please make sure that the email address(es) uses only valid characters.")
    if len(subj) == 0:
        raise RuntimeError("Cannot send an email with a blank subject!")
    if len(messages) == 0:
        raise RuntimeError("Cannot send an email with a blank message!")

    # Prepare the HTML email if enabled...
    template = env.get_template(f'generic_email_template.html')
    template_vars = {
        "title": f"Automated Email",
        "username": to_user.lower().strip().title(),
        "messages": messages
    }
    html_out = template.render(template_vars)

    # Authenticate self first...
    auth_request = requests.post(f"{email_api}{THIRD_PARTY_ROUTES.Email.login}", data={
        "username": ConfigManager().config()['Email Settings']['pca_email_username'].strip(),
        "password": ConfigManager().config()['Email Settings']['pca_email_password'].strip()
    })
    resp_json = auth_request.json()
    access_token = resp_json['accessToken']

    # Configure authentication header...
    headers = {'Authorization': f'Bearer {access_token}'}
    # Configure email options...
    for email in to:
        email_opts = {
            "from": ConfigManager().config()['Email Settings']['pca_email_username'].strip(),
            "to": email,
            "subject": subj,
            "messageHTML": html_out,
            "messagePlainText": "\n".join(messages)
        }
        # Send the email...
        requests.post(f"{email_api}{THIRD_PARTY_ROUTES.Email.send_email}",
                      data=email_opts, headers=headers)
