from django.contrib import admin
from .models import (
    Paper,
    Training,
    TapisInfo,
    JobsData,
    TenantServiceUsage,
    TenantJobsData
)

# Register your models here.
admin.site.register(Paper)
admin.site.register(Training)
admin.site.register(TapisInfo)
admin.site.register(JobsData)
admin.site.register(TenantServiceUsage)
admin.site.register(TenantJobsData)
