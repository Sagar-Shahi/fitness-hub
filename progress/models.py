from django.conf import settings
from django.db import models

class ProgressRecord(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='progress')
    date = models.DateField()
    weight = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    body_fat = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    waist = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    chest = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    arm = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.user.username} — {self.date}"
