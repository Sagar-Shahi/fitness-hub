from django.db import models
from django.utils.text import slugify
from django.conf import settings


class Exercise(models.Model):
	DIFFICULTY = (('beginner', 'Beginner'), ('intermediate', 'Intermediate'), ('advanced', 'Advanced'))
	CATEGORY = (('chest', 'Chest'), ('back', 'Back'), ('shoulders', 'Shoulders'), ('arms', 'Arms'), ('legs', 'Legs'), ('core', 'Core'), ('cardio', 'Cardio'))

	GOAL_CHOICES = (
		('general', 'General'),
		('strength', 'Strength'),
		('hypertrophy', 'Hypertrophy'),
		('endurance', 'Endurance'),
		('mobility', 'Mobility'),
		('flexibility', 'Flexibility'),
		('weight_loss', 'Weight Loss'),
	)

	name = models.CharField(max_length=200)
	slug = models.SlugField(max_length=220, unique=True, blank=True)
	category = models.CharField(max_length=40, choices=CATEGORY)
	description = models.TextField(blank=True)
	target_muscles = models.CharField(max_length=200, blank=True)
	difficulty = models.CharField(max_length=20, choices=DIFFICULTY, default='beginner')
	equipment = models.CharField(max_length=200, blank=True)
	image_url = models.URLField(blank=True)
	video_url = models.URLField(blank=True)
	goal = models.CharField(max_length=30, choices=GOAL_CHOICES, default='general')
	default_reps = models.PositiveSmallIntegerField(default=10)
	default_sets = models.PositiveSmallIntegerField(default=3)
	duration_min = models.PositiveSmallIntegerField(default=5)
	calories_per_set = models.PositiveSmallIntegerField(default=8)
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


class ExerciseCompletion(models.Model):
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='exercise_completions')
	exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name='completions')
	date = models.DateField(auto_now_add=True)
	reps = models.PositiveIntegerField(null=True, blank=True)
	hold_time_sec = models.PositiveIntegerField(null=True, blank=True)
	notes = models.TextField(blank=True)

	class Meta:
		ordering = ['-date']

	def __str__(self):
		return f"{self.user.username} — {self.exercise.name} — {self.date}"
