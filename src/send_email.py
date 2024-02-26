import os
import sys
import argparse
import django
import datetime as date
import logging

logger = logging.getLogger(__name__)

os.environ["DJANGO_SETTINGS_MODULE"] = "reporter.settings"
django.setup()

from reporter.helpers import generate_email_data
from reporter.apps.main.models import Service, Tenant
from reporter.apps.jupyterhub.utils import send_jupyterhub_email

parser = argparse.ArgumentParser(description='Process arguments for email')
parser.add_argument('service')
parser.add_argument('tenant')
args = parser.parse_args()

services = Service.objects.all().values('name')
valid_services = [service['name'] for service in list(services)]

if args.service not in valid_services:
    logger.error(
        f'{args.service} not valid service, expecting one of: {valid_services}'
    )
    sys.exit()

service = Service.objects.get(pk=args.service)
tenants = service.tenant_set.all()

service_tenants = [tenant.name for tenant in tenants]

if args.tenant not in service_tenants:
    sys.exit()

tenant = Tenant.objects.get(pk=args.tenant)

if __name__ == '__main__':
    week_end = date.date.today() - date.timedelta(days=1)
    week_begin = week_end - date.timedelta(days=6)

    match args.service:
        case 'jupyterhub':
            data = generate_email_data(service, tenant, week_begin, week_end)
            send_jupyterhub_email(data, week_begin, week_end)
        case 'tapis':
            pass
        case _:
            logger.error(f"Email sender not configured for {args.service}")
            pass
