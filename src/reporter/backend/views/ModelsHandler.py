from ...apps.main.models import Service, Admin, Tenant, TenantDirectory, TenantRecipient


def save_service(service):
    ser = Service(name=service["name"])
    ser.save()
    if "admins" in service and service["admins"] != []:
        save_admins(ser, service["admins"])

    if "tenants" in service and service["tenants"] != []:
        save_tenants(ser, service["tenants"])


def save_admins(ser, admins):
    for admin in admins:
        entry = Admin(service=ser, user=admin)
        entry.save()


def save_tenants(ser, tenants):
    for tenant in tenants:
        entry = Tenant(
            service=ser,
            name=tenant["name"],
            primary_receiver=tenant["primary_receiver"],
            proper_name=tenant["proper_name"],
        )
        entry.save()

        if "directories" in tenant:
            save_directories(entry, tenant["directories"])

        if "recipients" in tenant:
            save_recipients(entry, tenant["recipients"])


def save_directories(entry, directories):
    for directory in directories:
        dir = TenantDirectory(tenant=entry, directory=directory)
        dir.save()


def save_recipients(entry, recipients):
    for recipient in recipients:
        rec = TenantRecipient(tenant=entry, recipient=recipient)
        rec.save()
