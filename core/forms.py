from django import forms
from .models import GameLog

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
                'rows': 3
            }),
            'rating': forms.NumberInput(attrs={
                'class': 'w-full p-3 bg-gray-800 text-white text-lg border border-gray-600 rounded-lg transition-all duration-300 ease-in-out focus:border-blue-500 focus:ring focus:ring-blue-300/50 bg-gradient-to-br from-gray-700/20 to-gray-800/30 hover:shadow-lg hover:shadow-blue-500/30'
            }),
            'hours_played': forms.NumberInput(attrs={
                'class': 'w-full p-3 bg-gray-800 text-white text-lg border border-gray-600 rounded-lg transition-all duration-300 ease-in-out focus:border-blue-500 focus:ring focus:ring-blue-300/50 bg-gradient-to-br from-gray-700/20 to-gray-800/30 hover:shadow-lg hover:shadow-blue-500/30'
            }),
        }
