from django import forms
from django.forms import ModelForm
from question.models import QuestionFile
from django.forms import ClearableFileInput

class BroadcastForm(forms.Form):
    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
    broadcast_text = forms.CharField(widget=forms.Textarea)

class QuestionForm(ModelForm):
    class Meta:
        model = QuestionFile
        fields = ['file']
        widgets = {
            "file": ClearableFileInput(attrs={'multiple': True}),
        }