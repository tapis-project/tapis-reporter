import os

import django

os.environ["DJANGO_SETTINGS_MODULE"] = "reporter.settings"
django.setup()

from reporter.configs import services
from reporter.backend.views import parse_config


def add_service_configs():
    for config in services:
        parse_config(config)

if __name__ == '__main__':
    add_service_configs()

