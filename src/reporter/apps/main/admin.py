from django.contrib import admin
from .models import Service, Admin, Tenant, TenantDirectory, TenantRecipient


# Register your models here.
admin.site.register(Service)
admin.site.register(Admin)
admin.site.register(Tenant)
admin.site.register(TenantDirectory)
admin.site.register(TenantRecipient)