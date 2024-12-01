from django import forms
from django.contrib.auth.forms import UserCreationForm

from captcha.fields import ReCaptchaField
from captcha.widgets import ReCaptchaV2Checkbox
from phonenumber_field.formfields import PhoneNumberField

from userauths.models import User

USER_TYPE = (
    ('Vendor', 'Vendor'),
    ('Customer', 'Customer'),
)


class UserRegisterForm(UserCreationForm):
    full_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-group', 'placeholder': 'Full Name'}), required=True)
    mobile = PhoneNumberField(widget=forms.TextInput(attrs={'class': 'form-group', 'placeholder': 'Phone Number'}), required=True)
    email = forms.EmailField(widget=forms.TextInput(attrs={'class': 'form-group', 'placeholder': 'Email'}), required=True)
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-group', 'placeholder': 'Password'}), required=True)
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-group', 'placeholder': 'Confirm Password'}), required=True)
    captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox())
    user_type = forms.ChoiceField(choices=USER_TYPE, widget=forms.Select(attrs={'class': 'form-select'}))

    class Meta:
        model = User
        fields = ['full_name', 'mobile', 'email', 'password1', 'password2', 'captcha', 'user_type']


class LoginForm(forms.Form):
    email = forms.EmailField(widget=forms.TextInput(attrs={'class': 'form-group', 'placeholder': 'Email'}), required=True)
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-group', 'placeholder': 'Password'}), required=True)
    captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox())

    class Meta:
        model = User
        fields = ['email', 'password', 'captcha']