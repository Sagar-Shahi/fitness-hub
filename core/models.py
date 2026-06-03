from django.db import models

# Core helpers - extend as needed
class SiteSetting(models.Model):
    key = models.CharField(max_length=120, unique=True)
    value = models.TextField(blank=True)

    def __str__(self):
        return self.key
