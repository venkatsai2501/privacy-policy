from django import forms
from .models import TrackedSite  # Assuming TrackedSite is your model for the tracked URLs

class URLForm(forms.ModelForm):
    class Meta:
        model = TrackedSite
        fields = ['title', 'url','logourl']
        labels = {
            'title': 'Website Title',
            'url': 'Website URL',
            'logourl':'Website Logo URL'
        }
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Enter website title'}),
            'url': forms.URLInput(attrs={'placeholder': 'Enter full URL (https://...)'}),
            'logourl': forms.HiddenInput(),  # Hidden input for the logo URL
            
        }
