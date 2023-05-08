import os

import django

os.environ["DJANGO_SETTINGS_MODULE"] = "reporter.settings"
django.setup()

from reporter.configs import services
from reporter.backend.views import save_service


def add_service_configs():
    for service in services:
        save_service(service)

if __name__ == '__main__':
    add_service_configs()

