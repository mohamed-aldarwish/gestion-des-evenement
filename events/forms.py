from django import forms
from django.utils import timezone

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

    def clean_event_date(self):
        event_date = self.cleaned_data['event_date']
        if event_date < timezone.localdate():
            raise forms.ValidationError("Event date cannot be in the past.")
        return event_date

    def clean_price(self):
        price = self.cleaned_data['price']
        if price <= 0:
            raise forms.ValidationError("Ticket price must be greater than zero.")
        return price

    def clean_capacity(self):
        capacity = self.cleaned_data['capacity']
        if self.instance and self.instance.pk:
            booked_seats = self.instance.booked_seats
            if capacity < booked_seats:
                raise forms.ValidationError(
                    f"Capacity cannot be lower than the {booked_seats} paid booked seat(s)."
                )
        return capacity
