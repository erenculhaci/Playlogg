from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from .models import Profile, GameLog
from django.contrib.auth.forms import PasswordResetForm as DjangoPasswordResetForm
from django.contrib.auth.forms import SetPasswordForm as DjangoSetPasswordForm

class PasswordResetForm(DjangoPasswordResetForm):
    """Custom password reset form with styled email field"""
    email = forms.EmailField(
        label='Email',
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'mt-1 block w-full rounded-md bg-gray-800 border border-gray-700 shadow-sm py-2 px-3 text-white focus:outline-none focus:ring-purple-500 focus:border-purple-500',
            'placeholder': 'Enter your email address'
        })
    )

class SetPasswordForm(DjangoSetPasswordForm):
    """Custom set password form with styled password fields"""
    new_password1 = forms.CharField(
        label="New password",
        widget=forms.PasswordInput(attrs={
            'class': 'mt-1 block w-full rounded-md bg-gray-800 border border-gray-700 shadow-sm py-2 px-3 text-white focus:outline-none focus:ring-purple-500 focus:border-purple-500',
            'placeholder': 'Enter new password'
        }),
    )
    new_password2 = forms.CharField(
        label="Confirm new password",
        widget=forms.PasswordInput(attrs={
            'class': 'mt-1 block w-full rounded-md bg-gray-800 border border-gray-700 shadow-sm py-2 px-3 text-white focus:outline-none focus:ring-purple-500 focus:border-purple-500',
            'placeholder': 'Confirm new password'
        }),
    )

class CustomPasswordChangeForm(PasswordChangeForm):
    """Custom password change form with styled fields"""
    old_password = forms.CharField(
        label="Current password",
        widget=forms.PasswordInput(attrs={
            'class': 'mt-1 block w-full rounded-md bg-gray-800 border border-gray-700 shadow-sm py-2 px-3 text-white focus:outline-none focus:ring-purple-500 focus:border-purple-500',
            'placeholder': 'Enter your current password'
        }),
    )
    new_password1 = forms.CharField(
        label="New password",
        widget=forms.PasswordInput(attrs={
            'class': 'mt-1 block w-full rounded-md bg-gray-800 border border-gray-700 shadow-sm py-2 px-3 text-white focus:outline-none focus:ring-purple-500 focus:border-purple-500',
            'placeholder': 'Enter new password'
        }),
    )
    new_password2 = forms.CharField(
        label="Confirm new password",
        widget=forms.PasswordInput(attrs={
            'class': 'mt-1 block w-full rounded-md bg-gray-800 border border-gray-700 shadow-sm py-2 px-3 text-white focus:outline-none focus:ring-purple-500 focus:border-purple-500',
            'placeholder': 'Confirm new password'
        }),
    )


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email']


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['profile_picture', 'first_name', 'last_name', 'bio']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
        }

class GameLogForm(forms.ModelForm):
    class Meta:
        model = GameLog
        fields = ['status', 'notes', 'rating', 'hours_played']
        widgets = {
            'status': forms.Select(attrs={
                'class': 'w-full p-3 bg-gray-800 text-white text-lg border border-gray-600 rounded-lg transition-all duration-300 ease-in-out focus:border-blue-500 focus:ring focus:ring-blue-300/50 bg-gradient-to-br from-gray-700/20 to-gray-800/30 hover:shadow-lg hover:shadow-blue-500/30 appearance-none cursor-pointer',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full p-3 bg-gray-800 text-white text-lg border border-gray-600 rounded-lg transition-all duration-300 ease-in-out focus:border-blue-500 focus:ring focus:ring-blue-300/50 bg-gradient-to-br from-gray-700/20 to-gray-800/30 hover:shadow-lg hover:shadow-blue-500/30',
                'rows': 3,
                'placeholder': 'Enter your notes here...'
            }),
            'rating': forms.NumberInput(attrs={
                'class': 'w-full p-3 bg-gray-800 text-white text-lg border border-gray-600 rounded-lg transition-all duration-300 ease-in-out focus:border-blue-500 focus:ring focus:ring-blue-300/50 bg-gradient-to-br from-gray-700/20 to-gray-800/30 hover:shadow-lg hover:shadow-blue-500/30',
                'min': 0,
                'max': 5,
                'step': 0.5,
                'placeholder': 'Enter your rating here...'
            }),
            'hours_played': forms.NumberInput(attrs={
                'class': 'w-full p-3 bg-gray-800 text-white text-lg border border-gray-600 rounded-lg transition-all duration-300 ease-in-out focus:border-blue-500 focus:ring focus:ring-blue-300/50 bg-gradient-to-br from-gray-700/20 to-gray-800/30 hover:shadow-lg hover:shadow-blue-500/30',
                'min': 0,
                'placeholder': 'Enter your hours played here...',
                'step': 5,
            }),
        }
