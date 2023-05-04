import os

import django

os.environ["DJANGO_SETTINGS_MODULE"] = "reporter.settings"
django.setup()

from reporter.apps.jupyterhub.models import Tenant, TenantDirectory, TenantRecipient
from reporter.configs import tenants


def add_tenant_configs():
    for conf in tenants:
        tenant = conf['name']
        primary_receiver = conf['primary_receiver']
        proper_name = conf['proper_name']
        entry = Tenant(
            tenant=tenant,
            primary_receiver=primary_receiver,
            proper_name=proper_name
        )
        entry.save()
        directories = conf['directories']
        recipients = conf['recipients']
        for directory in directories:
            dir = TenantDirectory(
                tenant=entry,
                directory=directory
            )
            dir.save()
        for recipient in recipients:
            rec = TenantRecipient(
                tenant=entry,
                recipient=recipient
            )
            rec.save()

if __name__ == '__main__':
    add_tenant_configs()

