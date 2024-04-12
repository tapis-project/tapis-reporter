import os
import django
import logging

logger = logging.getLogger(__name__)

os.environ["DJANGO_SETTINGS_MODULE"] = "reporter.settings"
django.setup()
from ..jupyterhub.utils import build_jupyterhub_email
from ..tapis.utils import build_tapis_email


def call_service_email_builder(service, data):
    match service.name:
        case "jupyterhub":
            message = build_jupyterhub_email(data)
            return message
        case "tapis":
            message = build_tapis_email(data)
            return message
        case _:
            return
