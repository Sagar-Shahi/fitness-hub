from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError

User = get_user_model()


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, max_length=254)
    # Bot trap: people never see this field (it is hidden with CSS), most bots fill in every field.
    website = forms.CharField(required=False, label='Leave this field empty', widget=forms.TextInput(
        attrs={'tabindex': '-1', 'autocomplete': 'off'}
    ))

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email')

    def clean_website(self):
        if self.cleaned_data.get('website'):
            raise ValidationError('Something went wrong. Please try again.')
        return ''

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError('That username is already taken.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError('An account with that email address already exists.')
        return email


class CaseInsensitiveAuthenticationForm(AuthenticationForm):
    """Logs in 'Sagar' and 'sagar' as the same person, and can refuse the attempt when locked out."""

    LOCKED_MESSAGE = 'Too many failed login attempts. Please wait a few minutes and try again.'

    def __init__(self, *args, locked=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.locked = locked

    def clean(self):
        if self.locked:
            raise ValidationError(self.LOCKED_MESSAGE, code='locked')  # the password is never even checked
        username = (self.cleaned_data.get('username') or '').strip()
        if username:
            match = User.objects.filter(username__iexact=username).only('username').first()
            if match is not None:
                self.cleaned_data['username'] = match.username
        return super().clean()


class ApiKeyForm(forms.Form):
    name = forms.CharField(
        max_length=60, label='Key name',
        help_text='What this key is for, for example "Zapier" or "Spreadsheet script".',
    )

    def clean_name(self):
        return self.cleaned_data['name'].strip()
