from django.db import transaction
from django.utils import timezone

from .email_utils import send_waitlist_available_email
from .models import Waitlist


def join_event_waitlist(user, event):
    waitlist_entry, created = Waitlist.objects.get_or_create(
        user=user,
        event=event,
        defaults={'status': 'waiting'}
    )

    if not created and waitlist_entry.status in ['cancelled', 'converted']:
        waitlist_entry.status = 'waiting'
        waitlist_entry.notified_at = None
        waitlist_entry.save(update_fields=['status', 'notified_at'])
        created = True

    return waitlist_entry, created


def notify_next_waitlisted_user(event):
    with transaction.atomic():
        next_waitlist = (
            Waitlist.objects.select_for_update()
            .filter(event=event, status='waiting')
            .select_related('user', 'event')
            .order_by('created_at')
            .first()
        )

        if not next_waitlist:
            return None

        email_sent = send_waitlist_available_email(
            next_waitlist.user,
            event
        )

        if not email_sent:
            return None

        next_waitlist.status = 'notified'
        next_waitlist.notified_at = timezone.now()
        next_waitlist.save(update_fields=['status', 'notified_at'])

        return next_waitlist
