import os
import argparse
import django
import logging

os.environ["DJANGO_SETTINGS_MODULE"] = "reporter.settings"
django.setup()

from reporter.apps.main.models import Service
from reporter.helpers import LogParser

logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser(description="Optional arguments for parsing logs")
parser.add_argument("-sd", "--start_date")
parser.add_argument("-ed", "--end_date")
parser.add_argument("-sv", "--service")
args = parser.parse_args()

if __name__ == "__main__":
    if args.service is not None:
        logParser = LogParser(args.service, args)
        logParser.parse_logs()

    else:
        services = Service.objects.values("name")
        for service in services:
            # Either splunk or NGINX file
            # Will be run daily
            logParser = LogParser(service["name"], args)
            logParser.parse_logs()
