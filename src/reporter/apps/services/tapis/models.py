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
        unique_together = ['title', 'primary_author']

    def savepaper(self):
        self.save()

    def __str__(self):
        return self.title + " " + self.primary_author


class TrainingData(models.Model):
    seminar = models.CharField(max_length=255)
    num_systems = models.IntegerField()


class TapisInfo(models.Model):
    num_tokens = models.IntegerField()
    num_unique_users = models.IntegerField()
    num_ctr_apps = models.IntegerField()


class TenantInfo(TapisInfo):
    tenant = models.CharField(max_length=255, primary_key=True)


class JobsData(models.Model):
    avg_daily_jobs = models.IntegerField()
    dev_daily_jobs = models.CharField(max_length=50)
    total_jobs = models.IntegerField()


class TenantServiceUsage(models.Model):
    log_day = models.IntegerField()
    log_month = models.IntegerField()
    log_year = models.IntegerField()
    start_time = models.CharField(max_length=10)
    end_time = models.CharField(max_length=10)
    tenant = models.CharField(max_length=100)
    service = models.CharField(max_length=50)
    log_count = models.IntegerField()

    class Meta:
        unique_together = ['log_day', 'log_month', 'log_year', 'start_time', 'end_time', 'tenant', 'service', 'log_count']

    def savesplunkdata(self):
        self.save()

    def __str__(self):
        return f"{self.log_day}/{self.log_month}/{self.log_year}\
            {self.start_time}-{self.end_time} {self.tenant} {self.service}\
            {self.log_count}"
