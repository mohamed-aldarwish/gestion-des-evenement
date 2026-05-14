import stripe
from registrations.views import send_reservation_email
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.views.decorators.http import require_POST
from events.models import Waitlist, Event
from django.utils import timezone
from datetime import timedelta
from .models import Ticket


stripe.api_key = settings.STRIPE_SECRET_KEY


@login_required
def ticket_detail(request, id):
    ticket = get_object_or_404(
        Ticket.objects.select_related('event', 'user'),
        id=id
    )

    if ticket.user != request.user and not request.user.is_superuser:
        return HttpResponseForbidden("Access denied")

    return render(request, 'tickets/ticket_detail.html', {
        'ticket': ticket
    })


@login_required
def payment_page(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    waitlist_entry = Waitlist.objects.filter(
        user=request.user,
        event=event,
        status='notified'
    ).first()

    can_pay = event.remaining_seats > 0 or waitlist_entry

    if not can_pay:
        return HttpResponseForbidden("No seats available.")

    return render(request, 'tickets/payment_page.html', {
        'event': event,
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
        'amount': event.price,
    })


@login_required
@require_POST
def create_payment_intent(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    waitlist_entry = Waitlist.objects.filter(
        user=request.user,
        event=event,
        status='notified'
    ).first()

    can_pay = event.remaining_seats > 0 or waitlist_entry

    if not can_pay:
        return JsonResponse({
            'error': 'No seats available.'
        }, status=403)

    intent = stripe.PaymentIntent.create(
        amount=int(event.price * 100),
        currency='usd',
        metadata={
            'event_id': event.id,
            'user_id': request.user.id,
        },
    )

    return JsonResponse({
        'clientSecret': intent.client_secret
    })


@login_required
def payment_success(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    waitlist_entry = Waitlist.objects.filter(
        user=request.user,
        event=event,
        status='notified'
    ).first()

    can_confirm = event.remaining_seats > 0 or waitlist_entry

    if not can_confirm:
        return HttpResponseForbidden("No seats available.")

    recent_ticket = Ticket.objects.filter(
        user=request.user,
        event=event,
        status='active',
        booked_at__gte=timezone.now() - timedelta(seconds=10)
    ).first()

    if recent_ticket:
        return redirect('ticket_detail', id=recent_ticket.id)

    ticket = Ticket.objects.create(
        user=request.user,
        event=event,
        quantity=1,
        status='active',
        payment_status='paid',
        amount=event.price
    )

    if waitlist_entry:
        waitlist_entry.status = 'cancelled'
        waitlist_entry.save(update_fields=['status'])

    try:
        send_reservation_email(request.user, ticket)
    except Exception as e:
        print("SENDGRID PAYMENT EMAIL ERROR:", e)

    return redirect('ticket_detail', id=ticket.id)


def payment_cancel(request):
    return render(request, 'tickets/payment_cancel.html')