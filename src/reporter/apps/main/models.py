from django.db import models


# Create your models here.

class Service(models.Model):
    name = models.CharField(max_length=255, primary_key=True)
    source = models.CharField(max_length=255)

    class Meta:
        unique_together = ('name', 'source')

    def __str__(self):
        return self.name


class Admin(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    user = models.CharField(max_length=255)

    class Meta:
        unique_together = ['service', 'user']

    def __str__(self):
        return self.service.name + " " + self.user


class Tenant(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, primary_key=True)
    primary_receiver = models.EmailField()
    proper_name = models.CharField(max_length=255)

    def saveserviceconfig(self):
        self.save()

    def __str__(self):
        return self.name


class TenantDirectory(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    directory = models.CharField(max_length=255)

    def saveservicedirectory(self):
        self.save()

    def __str__(self):
        return self.tenant.name + " " + self.directory

    class Meta:
        verbose_name_plural = "Tenant Directories"


class TenantRecipient(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    recipient = models.EmailField()

    def saveservicerecipient(self):
        self.save()

    def __str__(self):
        return self.tenant.name + " " + self.recipient

    class Meta:
        verbose_name_plural = "Tenant Recipients"
