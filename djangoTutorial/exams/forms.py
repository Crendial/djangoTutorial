from django import forms
from .models import Student


class IdentifyForm(forms.Form):
    name = forms.CharField(max_length=100, label="Your name")

    def clean_name(self):
        name = " ".join(self.cleaned_data["name"].split())
        if Student.objects.filter(name__iexact=name).exists():
            raise forms.ValidationError("That name is taken.")
        return name
