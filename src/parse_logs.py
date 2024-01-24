import os
import django
import logging

os.environ["DJANGO_SETTINGS_MODULE"] = "reporter.settings"
django.setup()

from reporter.apps.main.models import Service
from reporter.helpers import LogParser

logger = logging.getLogger(__name__)


if __name__ == '__main__':
    services = Service.objects.values('name')

    for service in services:
        # Either splunk or NGINX file
        # Will be run daily
        print(service)
        logParser = LogParser(service['name'])
        logParser.parse_logs()
