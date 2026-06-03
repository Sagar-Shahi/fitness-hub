from django import forms
from .models import Goal

FOCUS_CHOICES = [
    ('Shoulders', 'Shoulders'),
    ('Back', 'Back'),
    ('Core', 'Core'),
    ('Legs', 'Legs'),
]


class GoalForm(forms.ModelForm):
    focus_areas = forms.MultipleChoiceField(
        choices=FOCUS_CHOICES,
        widget=forms.MultipleHiddenInput,
        required=False,
    )

    class Meta:
        model = Goal
        fields = ('goal_type', 'target_weight', 'timeline_weeks', 'description')
        widgets = {
            'goal_type': forms.HiddenInput(),
            'target_weight': forms.NumberInput(
                attrs={
                    'class': 'input-control',
                    'placeholder': 'e.g. 75',
                    'min': '0',
                    'step': '0.1',
                }
            ),
            'timeline_weeks': forms.NumberInput(
                attrs={
                    'class': 'input-control',
                    'placeholder': 'e.g. 12',
                    'min': '1',
                }
            ),
            'description': forms.Textarea(
                attrs={
                    'class': 'input-control textarea-control',
                    'rows': 3,
                    'placeholder': 'Define the purpose and milestones for this goal.',
                }
            ),
        }
        labels = {
            'target_weight': 'Target Weight',
            'timeline_weeks': 'Timeline (weeks)',
            'description': 'Specific Objectives',
        }
