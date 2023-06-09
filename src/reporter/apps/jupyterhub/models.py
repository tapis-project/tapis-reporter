from django.conf import settings
from django.db import models
from django.utils import timezone

# Create your models here.

class Log(models.Model):
    tenant = models.CharField(max_length=255)
    user = models.CharField(max_length=255)
    date = models.DateField()
    time = models.TimeField()

    class Meta:
        abstract = True

class FileLog(Log):
    action = models.CharField(max_length=255)
    filepath = models.TextField()
    filename = models.CharField(max_length=255)
    raw_filepath = models.TextField()

    class Meta:
        unique_together = ['tenant', 'user', 'action', 'filepath', 'filename', 'date', 'time', 'raw_filepath']
    
    def savefilelog(self):
        self.save()

    def __str__(self):
        return self.tenant + " " + self.user + " " + self.action + " " + self.filepath + " " + self.filename + " " + str(self.date) + " " + str(self.time)

class LoginLog(Log):
    class Meta:
        unique_together = ['tenant', 'user', 'date', 'time']

    def saveloginlog(self):
        self.save()
    
    def __str__(self):
        return self.tenant + " " + self.user + " " + str(self.date) + " " + str(self.time)

class ParsedAccessLog(models.Model):
    filename = models.CharField(max_length=255, primary_key=True)
    status = models.CharField(max_length=255)
    last_line_added = models.IntegerField(default=0)
    error = models.TextField(default='')
    
    def saveparsedlog(self):
        self.save()

    def __str__(self):
        return self.filename + " " + self.status + " " + str(self.last_line_added)

class Tenant(models.Model):
    tenant = models.CharField(max_length=255, primary_key=True)
    primary_receiver = models.EmailField()
    proper_name = models.CharField(max_length=255)

    def savetenantconfig(self):
        self.save()
    
    def __str__(self):
        return self.tenant + " " + self.primary_receiver

class TenantDirectory(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    directory = models.CharField(max_length=255)

    def savetenantdirectory(self):
        self.save()

    def __str__(self):
        return self.tenant.tenant + " " + self.directory
    
    class Meta:
        verbose_name_plural = "Tenant Directories"

class TenantRecipient(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    recipient = models.EmailField()

    def savetenantrecipient(self):
        self.save()

    def __str__(self):
        return self.tenant.tenant + " " + self.recipient
    
    class Meta:
        verbose_name_plural = "Tenant Recipients"
