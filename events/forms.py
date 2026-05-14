from django import forms
from .models import Event


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            'title',
            'description',
            'event_date',
            'event_time',
            'price',
            'location',
            'capacity',
            'category',
            'image',
            'status',
        ]