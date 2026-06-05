from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import (
    PasswordChangeForm,
    UserCreationForm,
)
from django.contrib.auth.models import User
from .models import Profile


USERNAME_HELP = (
    '150 characters or fewer. Letters, digits and @/./+/-/_ only. '
    'Case-sensitive.'
)


class AccountSettingsForm(forms.ModelForm):
    """Edit username, first name, last name, and email from one place."""

    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')
        help_texts = {'username': USERNAME_HELP}

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            css = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = (css + ' settings-input').strip()
        self.fields['first_name'].required = False
        self.fields['last_name'].required = False
        self.fields['email'].required = True

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        if not username:
            raise forms.ValidationError('Username is required.')
        qs = User.objects.filter(username__iexact=username)
        if self.user is not None:
            qs = qs.exclude(pk=self.user.pk)
        if qs.exists():
            raise forms.ValidationError('That username is already taken.')
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        qs = User.objects.filter(email__iexact=email)
        if self.user is not None:
            qs = qs.exclude(pk=self.user.pk)
        if qs.exists():
            raise forms.ValidationError('That email is already registered to another account.')
        return email


class StyledPasswordChangeForm(PasswordChangeForm):
    """Same validation as Django's built-in PasswordChangeForm, with our CSS class."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            css = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = (css + ' settings-input').strip()
            field.widget.attrs.setdefault('autocomplete', 'current-password' if name == 'old_password' else 'new-password')


class UserRegistrationForm(UserCreationForm):
    age = forms.IntegerField(required=True, min_value=1, label='Age')
    height_ft = forms.DecimalField(
        required=True,
        max_digits=4,
        decimal_places=2,
        min_value=1.0,
        max_value=9.0,
        label='Height (ft)',
        help_text='Enter your height in feet, e.g. 5.83 = 5 ft 10 in.',
    )
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
        fields = ('age', 'gender', 'height_ft', 'weight_kg', 'activity_level', 'body_type', 'selected_goal', 'goal_focus', 'bio')
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
