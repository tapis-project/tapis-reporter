from django.db import models

# Create your models here.

class Service(models.Model):
    name = models.CharField(max_length=255, primary_key=True)

class Admin(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, primary_key=True)

class Tenant(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    primary_receiver = models.EmailField()
    proper_name = models.CharField(max_length=255)

    def saveserviceconfig(self):
        self.save()
    
    def __str__(self):
        return self.service + " " + self.primary_receiver

class TenantDirectory(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    directory = models.CharField(max_length=255)

    def saveservicedirectory(self):
        self.save()

    def __str__(self):
        return self.service.service + " " + self.directory
    
    class Meta:
        verbose_name_plural = "Tenant Directories"

class TenantRecipient(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    recipient = models.EmailField()

    def saveservicerecipient(self):
        self.save()

    def __str__(self):
        return self.service.service + " " + self.recipient
    
    class Meta:
        verbose_name_plural = "Tenant Recipients"