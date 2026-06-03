from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile


class UserRegistrationForm(UserCreationForm):
    age = forms.IntegerField(required=True, min_value=1, label='Age')
    height_cm = forms.DecimalField(required=True, max_digits=5, decimal_places=2, label='Height (cm)')
    weight_kg = forms.DecimalField(required=True, max_digits=6, decimal_places=2, label='Weight (kg)')

    class Meta:
        model = User
        fields = ('username', 'password1', 'password2')


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('age', 'gender', 'height_cm', 'weight_kg', 'activity_level', 'body_type', 'selected_goal', 'goal_focus', 'bio')
        widgets = {
            'selected_goal': forms.RadioSelect,
            'goal_focus': forms.RadioSelect,
            'body_type': forms.RadioSelect,
        }


class GoalSelectionForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('selected_goal', 'goal_focus', 'body_type')
        labels = {
            'selected_goal': 'Primary Fitness Goal',
            'goal_focus': 'Focus Area',
            'body_type': 'Body Type',
        }
        widgets = {
            'selected_goal': forms.RadioSelect,
            'goal_focus': forms.RadioSelect,
            'body_type': forms.RadioSelect,
        }
