from django import forms
from django.conf import settings
from django.utils import timezone

from .models import BodyMetric, Exercise, Meal, Profile, Workout

DATE = forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d')


def _not_future(value):
    if value > timezone.localdate():
        raise forms.ValidationError('The date cannot be in the future.')
    return value


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['calorie_target', 'weekly_workout_target', 'target_weight_kg']
        labels = {'calorie_target': 'Daily calories (kcal)', 'weekly_workout_target': 'Workouts per week',
                  'target_weight_kg': 'Target weight (kg, optional)'}


class WorkoutForm(forms.ModelForm):
    class Meta:
        model = Workout
        fields = ['date', 'name', 'duration_min', 'notes']
        widgets = {'date': DATE, 'notes': forms.TextInput()}
        labels = {'duration_min': 'Duration (minutes)', 'name': 'Name'}

    def __init__(self, *args, owner=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.owner = owner

    def clean_date(self):
        return _not_future(self.cleaned_data['date'])

    def clean(self):
        data = super().clean()
        if self.instance.pk is None and self.owner is not None:
            if Workout.objects.filter(owner=self.owner).count() >= settings.MAX_WORKOUTS_PER_USER:
                raise forms.ValidationError(f'You have reached the limit of {settings.MAX_WORKOUTS_PER_USER} workouts.')
        return data


class ExerciseForm(forms.ModelForm):
    class Meta:
        model = Exercise
        fields = ['name', 'sets', 'reps', 'weight_kg']
        labels = {'weight_kg': 'Weight (kg)'}

    def __init__(self, *args, workout=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.workout = workout

    def clean(self):
        data = super().clean()
        if self.workout is not None and self.workout.exercises.count() >= settings.MAX_EXERCISES_PER_WORKOUT:
            raise forms.ValidationError(f'A workout can have at most {settings.MAX_EXERCISES_PER_WORKOUT} exercises.')
        return data


class WeightForm(forms.ModelForm):
    class Meta:
        model = BodyMetric
        fields = ['date', 'weight_kg']
        widgets = {'date': DATE}
        labels = {'weight_kg': 'Weight (kg)'}

    def clean_date(self):
        return _not_future(self.cleaned_data['date'])

    def validate_unique(self):  # saving the same day again simply replaces the value
        pass


class MealForm(forms.ModelForm):
    class Meta:
        model = Meal
        fields = ['date', 'kind', 'name', 'calories', 'protein_g', 'carbs_g', 'fat_g']
        widgets = {'date': DATE}
        labels = {'kind': 'Meal', 'calories': 'Calories (kcal)', 'protein_g': 'Protein (g)', 'carbs_g': 'Carbs (g)', 'fat_g': 'Fat (g)'}

    def __init__(self, *args, owner=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.owner = owner

    def clean_date(self):
        return _not_future(self.cleaned_data['date'])

    def clean(self):
        data = super().clean()
        day = data.get('date')
        if day and self.owner is not None and Meal.objects.filter(owner=self.owner, date=day).count() >= settings.MAX_MEALS_PER_DAY:
            raise forms.ValidationError(f'You can log at most {settings.MAX_MEALS_PER_DAY} meals per day.')
        return data
