from django import forms
from .models import Goal


class GoalForm(forms.ModelForm):
    class Meta:
        model = Goal
        fields = ('goal_type', 'target_weight', 'timeline_weeks', 'description')
