from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import transaction

from events.email_utils import send_ticket_confirmed_email
from events.models import Event, Waitlist
from .models import Ticket


class PaymentConfirmationError(Exception):
    pass


class PaymentNotSucceeded(PaymentConfirmationError):
    pass


class PaymentMetadataError(PaymentConfirmationError):
    pass


class AlreadyBookedError(PaymentConfirmationError):
    pass


class NoSeatsAvailableError(PaymentConfirmationError):
    pass





def normalize_payment_metadata(payment_intent):
    metadata = getattr(payment_intent, 'metadata', {}) or {}
    if hasattr(metadata, 'to_dict'):
        return metadata.to_dict()
    return dict(metadata)


def payment_amount_decimal(payment_intent):
    amount = (
        getattr(payment_intent, 'amount_received', None)
        or getattr(payment_intent, 'amount', 0)
        or 0
    )
    return Decimal(amount) / Decimal('100')




def user_can_start_payment(user, event):
    if Ticket.objects.filter(
        user=user,
        event=event,
        status='active',
        payment_status='paid'
    ).exists():
        return False, 'You already have a confirmed ticket for this event.'

    if event.remaining_seats <= 0:
        return False, 'No seats available for payment right now.'



    return True, ''


def confirm_paid_ticket(payment_intent, request_user=None):
    if payment_intent.status != 'succeeded':
        raise PaymentNotSucceeded('Payment was not completed.')

    metadata = normalize_payment_metadata(payment_intent)
    event_id = metadata.get('event_id')
    user_id = metadata.get('user_id')

    if not event_id or not user_id:
        raise PaymentMetadataError('Payment metadata is incomplete.')

    if request_user and str(request_user.id) != str(user_id):
        raise PaymentMetadataError('Payment does not belong to this user.')

    User = get_user_model()

    with transaction.atomic():
        event = Event.objects.select_for_update().get(id=event_id)
        user = User.objects.select_for_update().get(id=user_id)

        existing_payment_ticket = (
            Ticket.objects.select_for_update()
            .filter(
                stripe_session_id=payment_intent.id,
                payment_status='paid'
            )
            .first()
        )

        if existing_payment_ticket:
            return existing_payment_ticket, False

        existing_user_ticket = (
            Ticket.objects.select_for_update()
            .filter(
                user=user,
                event=event,
                status='active',
                payment_status='paid'
            )
            .first()
        )

        if existing_user_ticket:
            return existing_user_ticket, False

        waitlist_entry = (
            Waitlist.objects.select_for_update()
            .filter(user=user, event=event, status='notified')
            .first()
        )



        if event.remaining_seats <= 0:
            raise NoSeatsAvailableError('No seats are available.')

        ticket = Ticket.objects.create(
            user=user,
            event=event,
            quantity=1,
            status='active',
            payment_status='paid',
            amount=payment_amount_decimal(payment_intent) or event.price,
            stripe_session_id=payment_intent.id
        )

        if waitlist_entry:
            waitlist_entry.status = 'converted'
            waitlist_entry.save(update_fields=['status'])

    send_ticket_confirmed_email(user, ticket)
    return ticket, True


def cancel_paid_ticket(ticket):
    with transaction.atomic():
        locked_ticket = (
            Ticket.objects.select_for_update()
            .select_related('event')
            .get(
                id=ticket.id,
                user=ticket.user,
                status='active',
                payment_status='paid'
            )
        )
        locked_ticket.status = 'cancelled'
        locked_ticket.save(update_fields=['status'])
        event = locked_ticket.event

    notified_entry = notify_next_waitlisted_user(event)
    return locked_ticket, notified_entry
