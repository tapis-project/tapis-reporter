from django.contrib import admin
from .models import FileLog, LoginLog, ParsedAccessLog, Tenant, TenantDirectory, TenantRecipient

# Register your models here.
admin.site.register(FileLog)
admin.site.register(LoginLog)
admin.site.register(ParsedAccessLog)
admin.site.register(Tenant)
admin.site.register(TenantDirectory)
admin.site.register(TenantRecipient)