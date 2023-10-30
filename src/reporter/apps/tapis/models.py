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