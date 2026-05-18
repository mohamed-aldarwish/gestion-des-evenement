from django.contrib import admin
from .models import Event, Waitlist


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'organizer', 'event_date', 'capacity', 'status', 'price')
    list_filter = ('status', 'category', 'event_date')
    search_fields = ('title', 'location', 'organizer__username')


@admin.register(Waitlist)
class WaitlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'event', 'status', 'created_at', 'notified_at')
    list_filter = ('status', 'created_at', 'notified_at')
    search_fields = ('user__username', 'user__email', 'event__title')
