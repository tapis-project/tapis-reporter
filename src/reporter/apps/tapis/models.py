from django.db import models

# Create your models here.


class Paper(models.Model):
    title = models.TextField()
    primary_author = models.CharField(max_length=255)
    publication_source = models.TextField()
    publication_date = models.IntegerField()
    co_authors = models.TextField()
    citation_url = models.TextField()
    citations = models.IntegerField()

    class Meta:
        unique_together = ["title", "primary_author"]

    def savepaper(self):
        self.save()

    def __str__(self):
        return self.title + " " + self.primary_author


class TrainingData(models.Model):
    seminar = models.CharField(max_length=255)
    num_systems = models.IntegerField()


# Holds data pertaining to db data for all of tapis
class TapisInfo(models.Model):
    num_tokens = models.IntegerField()
    num_unique_users = models.IntegerField()
    num_ctr_apps = models.IntegerField()


# Holds data pertaining to db data for specific tenant
class TenantTapisInfo(TapisInfo):
    tenant = models.CharField(max_length=255, primary_key=True)


# Holds data pertaining to jobs db query
class JobsData(models.Model):
    avg_daily_jobs = models.IntegerField()
    dev_daily_jobs = models.CharField(max_length=50)
    total_jobs = models.IntegerField()
    num_using_smart_scheduling = models.IntegerField()


class TenantServiceUsage(models.Model):
    log_date = models.DateField()
    start_time = models.CharField(max_length=10)
    end_time = models.CharField(max_length=10)
    tenant = models.CharField(max_length=100)
    service = models.CharField(max_length=50)
    log_count = models.IntegerField()

    class Meta:
        unique_together = ["log_date", "start_time", "end_time", "tenant", "service"]

    def savetenantserviceusage(self):
        self.save()

    def __str__(self):
        return f"{self.log_date} {self.start_time}-{self.end_time} \
            {self.tenant} {self.service} {self.log_count}"
