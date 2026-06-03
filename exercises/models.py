from django.db import models
from django.utils.text import slugify


class Exercise(models.Model):
	DIFFICULTY = (('beginner', 'Beginner'), ('intermediate', 'Intermediate'), ('advanced', 'Advanced'))
	CATEGORY = (('chest', 'Chest'), ('back', 'Back'), ('shoulders', 'Shoulders'), ('arms', 'Arms'), ('legs', 'Legs'), ('core', 'Core'), ('cardio', 'Cardio'))

	name = models.CharField(max_length=200)
	slug = models.SlugField(max_length=220, unique=True, blank=True)
	category = models.CharField(max_length=40, choices=CATEGORY)
	description = models.TextField(blank=True)
	target_muscles = models.CharField(max_length=200, blank=True)
	difficulty = models.CharField(max_length=20, choices=DIFFICULTY, default='beginner')
	equipment = models.CharField(max_length=200, blank=True)
	image_url = models.URLField(blank=True)
	video_url = models.URLField(blank=True)
	steps = models.TextField(blank=True)
	form_tips = models.TextField(blank=True)
	breathing = models.TextField(blank=True)
	common_mistakes = models.TextField(blank=True)
	safety = models.TextField(blank=True)

	class Meta:
		ordering = ['name']

	def __str__(self):
		return self.name

	def save(self, *args, **kwargs):
		if not self.slug:
			self.slug = slugify(self.name)
		super().save(*args, **kwargs)
