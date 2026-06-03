from django import forms
from exercises.models import ExerciseCompletion


class ExerciseCompletionForm(forms.ModelForm):
    class Meta:
        model = ExerciseCompletion
        fields = ('reps', 'hold_time_sec', 'notes')
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3})
        }
