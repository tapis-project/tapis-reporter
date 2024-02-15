from django.contrib import admin
from .models import Paper, TrainingData, TapisInfo, TenantTapisInfo, JobsData, TenantServiceUsage

# Register your models here.
admin.site.register(Paper)
admin.site.register(TrainingData)
admin.site.register(TapisInfo)
admin.site.register(TenantTapisInfo)
admin.site.register(JobsData)
admin.site.register(TenantServiceUsage)