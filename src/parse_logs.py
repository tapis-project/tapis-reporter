import os
import django
import logging

from reporter.apps.main.models import Service
from reporter.helpers import LogParser

os.environ["DJANGO_SETTINGS_MODULE"] = "reporter.settings"
django.setup()

logger = logging.getLogger(__name__)


if __name__ == '__main__':
    services = Service.objects.values('name')

    for service in services:
        # Either splunk or NGINX file
        # Will be run daily
        logParser = LogParser(service['name'])
