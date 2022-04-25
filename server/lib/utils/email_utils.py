"""
This module contains utility functions related to the creation and sending
of emails using the SmarterMail API.
"""

import re
from typing import List
import requests
from jinja2 import Environment, FileSystemLoader

from server.lib.logging_manager import LoggingManager
from server.lib.config_manager import ConfigManager
from server.lib.strings import ROOT_DIR, LOG_ORIGIN_API
from server.web_api.api_routes import THIRD_PARTY_ROUTES

# Email validation regex
email_validator_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
env = Environment(loader=FileSystemLoader(
    [
        f'{ROOT_DIR}/lib/email_service'
    ]
))


def send_test_email():
    """
    This is a test method used to verify that communication between the python server and the SmarterMail API and mail server
    is working and fully functional by sending a test email from the server's SmarterMail account to itself.

    :return: A JSON-Compatible dictionary of the SmarterMail API response to sending a test email.
    :rtype: Dict[str, any]
    """
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


def send_email(to_user: str, to_email: List[str], subj: str, messages: List[str], template: str = None, to_cc: str = None) -> bool:
    """
    This utility method serves as an abstraction to the SmarterMails message-put endpoint to provide
    an integration with the python server to allow emails to be sent through SmarterEmail email servers easily.
    All email communications in this python server must utilize this utility method to send emails.

    :param to_user: The receiving user's name.
    :type to_user: str, required
    :param to_email: A list of all receiving user's email addresses.
    :type to_email: List[str], required
    :param subj: The subject text of the email.
    :type subj: str, required
    :param messages: A list of all the individual messages that should be formatted and rendered in the sent email.
    :type messages: List[str], required
    :param template: Optionally the email template can be specified by the file name. For example, leave requests use a different email template than generic emails.
    :type template: str, optional
    :param to_cc: Optionally a CC email address can be provided.
    :type to_cc: str, optional
    :return: True if the email was successfully formatted, rendered, and sent to the appropriate user(s).
    :rtype: bool
    :raises RuntimeError: If any of the provided parameters are invalid, or the email configuration settings in the server configuration file is invalid.
    """
    email_api = f"{'https://' if ConfigManager().config().getboolean('Email Settings', 'pca_email_use_https') else 'http://'}{ConfigManager().config()['Email Settings']['pca_email_api']}"
    # Validate provided information and email address.
    if None in (to_user, to_email, subj, messages):
        raise RuntimeError("Cannot send an email with the 'to', 'subject', or 'message' fields being blank!")
    if to_cc and isinstance(to_cc, str):
        to_cc = [to_cc]
    if to_email and isinstance(to_email, str):
        to_email = [to_email]
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
    if template is None:
        template = env.get_template(f'generic_email_template.html')
        template_vars = {
            "title": f"Automated Email",
            "username": to_user.lower().strip().title(),
            "messages": messages
        }
    else:
        template = env.get_template(template)
        template_vars = {
            "title": f"Automated Email",
            "message_title": to_user.lower().strip().title(),
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
        if to_cc:
            email_opts["cc"] = [", ".join(to_cc)]
        # Send the email...
        try:
            requests.post(f"{email_api}{THIRD_PARTY_ROUTES.Email.send_email}",
                          data=email_opts, headers=headers)
        except requests.exceptions.HTTPError:
            return False
    LoggingManager().log(LoggingManager.LogLevel.LOG_INFO,
                         f"An email was sent to the following email addresses: {', '.join([email for email in to])}.",
                         origin=LOG_ORIGIN_API, no_print=False)
    return True
