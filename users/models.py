from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(models.Model):
	GENDER_CHOICES = (('male', 'Male'), ('female', 'Female'), ('other', 'Other'))
	ACTIVITY_LEVELS = (
		('sedentary', 'Sedentary'),
		('light', 'Light'),
		('moderate', 'Moderate'),
		('active', 'Active'),
		('very_active', 'Very Active'),
	)

	user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
	age = models.PositiveIntegerField(null=True, blank=True)
	gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)
	height_cm = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
	weight_kg = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	activity_level = models.CharField(max_length=20, choices=ACTIVITY_LEVELS, blank=True)
	bio = models.TextField(blank=True)

	GOAL_CHOICES = (
		('calisthenics_body', 'Calisthenics Body'),
		('v_taper', 'V-Taper'),
		('weight_loss', 'Weight Loss'),
		('general_fitness', 'General Fitness'),
		('my_plan', 'My Plan'),
	)

	GOAL_FOCUS_CHOICES = (
		('upper_body', 'Upper Body'),
		('lower_body', 'Lower Body'),
		('core', 'Core Stability'),
		('pull_strength', 'Pull Strength'),
		('push_strength', 'Push Strength'),
		('mobility', 'Mobility'),
	)

	BODY_TYPES = (
		('lean', 'Lean'),
		('average', 'Average'),
		('stocky', 'Stocky'),
	)

	selected_goal = models.CharField(max_length=30, choices=GOAL_CHOICES, blank=True)
	goal_focus = models.CharField(max_length=30, choices=GOAL_FOCUS_CHOICES, blank=True)
	body_type = models.CharField(max_length=20, choices=BODY_TYPES, blank=True)

	def __str__(self):
		return f"Profile: {self.user.username}"


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
	if created:
		Profile.objects.create(user=instance)

