from django import forms
from .models import GameLog

class GameLogForm(forms.ModelForm):
    class Meta:
        model = GameLog
        fields = ['status', 'notes', 'rating', 'hours_played']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'rating': forms.NumberInput(attrs={'class': 'form-control'}),
            'hours_played': forms.NumberInput(attrs={'class': 'form-control'}),
        }
