from apps.main.models import Service, Admin, Tenant, TenantDirectory, TenantRecipient


def parse_config(config):
    save_services(config)

def save_services(config):
    service = Service(
        name = config['name']
    )
    service.save()
    save_admins(service, config['admins'])
    save_tenants(config['tenants'])

def save_admins(service, admins):
    for admin in admins:
        entry = Admin(
            service = service,
            name = admin
        )
        entry.save()

def save_tenants(tenants):
    for tenant in tenants:
        primary_receiver = tenant['primary_receiver']
        proper_name = tenant['proper_name']
        entry = Tenant(
            tenant = tenant,
            primary_receiver = primary_receiver,
            proper_name = proper_name
        )
        entry.save()
    save_directories(entry, tenants['directories'])
    save_recipients(entry, tenants['recipients'])

def save_directories(entry, config):
    directories = config['directories']
    for directory in directories:
        dir = TenantDirectory(
            tenant=entry,
            directory=directory
        )
        dir.save()

def save_recipients(entry, config):
    recipients = config['recipients']
    for recipient in recipients:
        rec = TenantRecipient(
            tenant=entry,
            recipient=recipient
        )
        rec.save()