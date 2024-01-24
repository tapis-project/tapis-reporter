from django.contrib import admin
from .models import FileLog, LoginLog, ParsedNginxFile

# Register your models here.
admin.site.register(FileLog)
admin.site.register(LoginLog)
admin.site.register(ParsedNginxFile)
