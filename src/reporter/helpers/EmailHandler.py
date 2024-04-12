import os
import datetime as date

import django
import logging
import smtplib

from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

os.environ["DJANGO_SETTINGS_MODULE"] = "reporter.settings"
django.setup()

from . import generate_email_data
from ..apps.helpers.utils import call_service_email_builder


class EmailHandler:
    """
    Handles emails being sent out
    """

    def __init__(self, service, tenant):
        self.sender = "no-reply@tacc.cloud"
        self.host = "relay.tacc.utexas.edu"
        self.port = 25
        self.service = service
        self.tenant = tenant

    def email_service(self):
        """
        Call EmailFunctions generate_email_data to retrieve data for email
        """
        data = self.build_email_data()
        message = call_service_email_builder(self.service, data)
        self.send_email(data, message)

    def build_email_data(self):
        week_end = date.date.today() - date.timedelta(days=1)
        week_begin = week_end - date.timedelta(days=6)

        data = generate_email_data(self.service, self.tenant, week_begin, week_end)
        data["week_begin"] = week_begin
        data["week_end"] = week_end

        return data

    def send_email(self, data: dict, message: MIMEMultipart):
        """ """
        receiver_emails = data["tenant_recipients"]

        try:
            server = smtplib.SMTP(self.host, self.port)
            server.sendmail(self.sender, receiver_emails, message.as_string())
            logger.info("Email sent successfully")
        except Exception as e:
            logger.debug(f"Error Sending Email: {e}")
