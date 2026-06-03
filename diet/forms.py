from django import forms
from .models import NutritionRecord


class NutritionRecordForm(forms.ModelForm):
    class Meta:
        model = NutritionRecord
        fields = ('date', 'calories', 'protein', 'carbs', 'fats', 'notes')
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'})
        }
