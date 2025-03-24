from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm
from .models import Profile, GameLog


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
