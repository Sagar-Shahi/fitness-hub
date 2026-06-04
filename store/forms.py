from django import forms
from .models import Order


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            'full_name', 'email', 'phone',
            'address', 'city', 'state', 'zip_code', 'country',
            'payment_method', 'notes',
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-input', 'placeholder': 'John Doe', 'required': True,
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-input', 'placeholder': 'you@example.com', 'required': True,
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-input', 'placeholder': '+1 (555) 000-0000',
            }),
            'address': forms.TextInput(attrs={
                'class': 'form-input', 'placeholder': '123 Main Street', 'required': True,
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-input', 'placeholder': 'New York', 'required': True,
            }),
            'state': forms.TextInput(attrs={
                'class': 'form-input', 'placeholder': 'NY', 'required': True,
            }),
            'zip_code': forms.TextInput(attrs={
                'class': 'form-input', 'placeholder': '10001', 'required': True,
            }),
            'country': forms.TextInput(attrs={
                'class': 'form-input', 'placeholder': 'United States', 'required': True,
            }),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-textarea', 'rows': 3,
                'placeholder': 'Delivery notes (optional)',
            }),
        }
