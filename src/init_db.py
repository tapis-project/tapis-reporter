import os
import django

from reporter.configs import services
from reporter.backend.views import save_service
from reporter.helpers import get_tapis_papers

os.environ["DJANGO_SETTINGS_MODULE"] = "reporter.settings"
django.setup()


def add_service_configs():
    for service in services:
        save_service(service)


if __name__ == '__main__':
    add_service_configs()
    get_tapis_papers()
