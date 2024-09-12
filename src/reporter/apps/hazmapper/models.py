from django.db import models

# Create your models here.


class HazmapperData(models.Model):
    user = models.TextField(max_length=255)
    date = models.DateField()
    time = models.CharField(max_length=10)
    application = models.TextField(max_length=255)
    map = models.TextField(max_length=255)
    is_public = models.BooleanField(default=False)
    project = models.TextField(max_length=255)
    published = models.BooleanField(default=False)

    class Meta:
        unique_together = ["user", "date", "time", "map"]

    def __str__(self):
        return self.user + " " + str(self.date) + ":" + self.time + " " + self.map

    def __eq__(self, other):
        if not isinstance(other, HazmapperData):
            return False
        return (self.user, self.date, self.time, self.map) == (
            other.user,
            other.date,
            other.time,
            other.map,
        )
