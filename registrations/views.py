from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from accounts.permissions import can_reserve_events
from events.email_utils import send_ticket_confirmed_email
from events.models import Event, Waitlist
from events.services import join_event_waitlist
from tickets.models import Ticket
from tickets.services import cancel_paid_ticket


def send_reservation_email(user, ticket):
    return send_ticket_confirmed_email(user, ticket)


@login_required
def register_event(request, event_id):
    event = get_object_or_404(Event, id=event_id, status='published')

    if request.method == "POST":
        if not can_reserve_events(request.user):
            messages.error(request, "Organizer and admin accounts cannot reserve tickets.")
            return redirect('event_detail', id=event.id)

        existing_ticket = Ticket.objects.filter(
            user=request.user,
            event=event,
            status='active',
            payment_status='paid'
        ).first()

        if existing_ticket:
            messages.info(request, "You already have a confirmed ticket for this event.")
            return redirect('ticket_detail', id=existing_ticket.id)

        if event.remaining_seats <= 0:
            waitlist_entry, created = join_event_waitlist(request.user, event)
            if created:
                messages.info(request, "The event is full. You have joined the waitlist.")
            elif waitlist_entry.status in ['waiting', 'notified']:
                messages.info(request, "You are already on the waitlist for this event.")
            else:
                messages.info(request, "Your waitlist request was restored.")

            return redirect('my_registrations')

        messages.info(request, "Please complete payment to confirm your ticket.")
        return redirect('payment_page', event_id=event.id)

    return render(request, 'events/book_ticket.html', {
        'event': event,
        'remaining_seats': event.remaining_seats
    })


@login_required
def my_registrations(request):
    tickets = (
        Ticket.objects.filter(
            user=request.user,
            status='active',
            payment_status='paid'
        )
        .select_related('event')
        .order_by('-booked_at')
    )

    waitlist_entries = (
        Waitlist.objects.filter(
            user=request.user,
            status__in=['waiting', 'notified']
        )
        .select_related('event')
        .order_by('-created_at')
    )

    return render(request, 'registrations/my_registrations.html', {
        'registrations': tickets,
        'waitlist_entries': waitlist_entries,
    })


@login_required
def cancel_registration(request, id):
    if request.method != "POST":
        return HttpResponseForbidden("Method not allowed")

    ticket = get_object_or_404(
        Ticket.objects.select_related('event'),
        id=id,
        user=request.user,
        status='active',
        payment_status='paid'
    )

    _, notified_entry = cancel_paid_ticket(ticket)

    if notified_entry:
        messages.info(request, "A seat is available. The first waitlisted user has been notified.")

    messages.success(request, "Reservation cancelled successfully.")
    return redirect('my_registrations')


@login_required
def cancel_waitlist(request, id):
    if request.method != "POST":
        return HttpResponseForbidden("Method not allowed")

    waitlist_entry = get_object_or_404(
        Waitlist,
        id=id,
        user=request.user,
        status__in=['waiting', 'notified']
    )

    waitlist_entry.status = 'cancelled'
    waitlist_entry.notified_at = None
    waitlist_entry.save(update_fields=['status', 'notified_at'])

    messages.success(request, "You left the waitlist.")
    return redirect('my_registrations')
