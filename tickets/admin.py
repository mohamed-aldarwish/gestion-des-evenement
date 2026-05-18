from django.contrib import admin
from .models import Ticket


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'event',
        'quantity',
        'status',
        'payment_status',
        'amount',
        'booked_at',
    )
    list_filter = ('status', 'payment_status', 'booked_at')
    search_fields = (
        'user__username',
        'user__email',
        'event__title',
        'stripe_session_id',
        'ticket_code',
    )
    readonly_fields = ('ticket_code', 'qr_code', 'booked_at')
