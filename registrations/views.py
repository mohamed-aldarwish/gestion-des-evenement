from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.conf import settings

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from events.models import Event, Waitlist
from tickets.models import Ticket


def send_reservation_email(user, ticket):
    if not user.email:
        return

    message = Mail(
        from_email=settings.DEFAULT_FROM_EMAIL,
        to_emails=user.email,
        subject=f"Reservation Confirmed - {ticket.event.title}",
        html_content=f"""
        <h2 style="color:#0f172a;">Reservation Confirmed 🎉</h2>

        <p>Hello <strong>{user.username}</strong>,</p>

        <p>
            Thank you for reserving your spot with <strong>EventFiY Events</strong>.
            Your reservation has been successfully confirmed.
        </p>

        <div style="background:#f8fafc; padding:20px; border-radius:12px; margin:20px 0;">
            <h3 style="margin-top:0; color:#d4af37;">Event Details</h3>

            <p><strong>Event:</strong> {ticket.event.title}</p>
            <p><strong>Date:</strong> {ticket.event.event_date}</p>
            <p><strong>Time:</strong> {ticket.event.event_time}</p>
            <p><strong>Location:</strong> {ticket.event.location}</p>
            <p><strong>Tickets:</strong> {ticket.quantity}</p>
            <p><strong>Ticket ID:</strong> {ticket.ticket_code}</p>
        </div>

        <p>Please keep this email for your records and present your QR ticket during entry.</p>
        <p>We look forward to seeing you at the event.</p>

        <br>

        <p>
            Best regards,<br>
            <strong>EventFiY Team</strong>
        </p>
        """
    )

    sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
    sg.send(message)


@login_required
def register_event(request, event_id):
    event = get_object_or_404(Event, id=event_id, status='published')

    if request.method == "POST":
        try:
            quantity = int(request.POST.get("quantity", 1))
        except ValueError:
            messages.error(request, "Quantité invalide.")
            return redirect('event_detail', id=event.id)

        if quantity <= 0:
            messages.error(request, "Quantité de tickets invalide.")
            return redirect('event_detail', id=event.id)

        existing_ticket = Ticket.objects.filter(
            user=request.user,
            event=event,
            status='active'
        ).first()

        if existing_ticket:
            if quantity > event.remaining_seats:
                messages.error(request, "Pas assez de places disponibles.")
                return redirect('event_detail', id=event.id)

            existing_ticket.quantity += quantity
            existing_ticket.save(update_fields=['quantity'])

            messages.success(request, "Votre réservation a été mise à jour.")
            return redirect('ticket_detail', id=existing_ticket.id)

        if quantity > event.remaining_seats:
            waitlist_entry, created = Waitlist.objects.update_or_create(
                user=request.user,
                event=event,
                defaults={
                    'quantity': quantity,
                    'status': 'waiting'
                }
            )

            messages.info(
                request,
                "L'événement est complet. Vous avez été ajouté à la liste d'attente."
            )

            return redirect('my_registrations')

        ticket = Ticket.objects.create(
            user=request.user,
            event=event,
            quantity=quantity,
            status='active'
        )

        try:
            send_reservation_email(request.user, ticket)
        except Exception as e:
            print("SENDGRID ERROR:", e)

        messages.success(request, f"Réservation confirmée pour {event.title}!")
        return redirect('ticket_detail', id=ticket.id)

    return render(request, 'events/book_ticket.html', {
        'event': event,
        'remaining_seats': event.remaining_seats
    })


@login_required
def my_registrations(request):
    tickets = Ticket.objects.filter(
        user=request.user,
        status='active'
    ).select_related('event').order_by('-booked_at')

    waitlist_entries = Waitlist.objects.filter(
        user=request.user,
        status__in=['waiting', 'notified']
    ).select_related('event').order_by('-created_at')

    return render(request, 'registrations/my_registrations.html', {
        'registrations': tickets,
        'waitlist_entries': waitlist_entries,
    })


@login_required
def cancel_registration(request, id):
    if request.method != "POST":
        return HttpResponseForbidden("Méthode non autorisée")

    ticket = get_object_or_404(
        Ticket,
        id=id,
        user=request.user,
        status='active'
    )

    event = ticket.event

    ticket.status = 'cancelled'
    ticket.save(update_fields=['status'])

    event.refresh_from_db()

    next_waitlist = (
        Waitlist.objects.filter(
            event=event,
            status='waiting'
        )
        .select_related('user', 'event')
        .order_by('created_at')
        .first()
    )

    if next_waitlist and next_waitlist.quantity <= event.remaining_seats:
        next_waitlist.status = 'notified'
        next_waitlist.save(update_fields=['status'])

        messages.info(
            request,
            "Une place est disponible. Le premier utilisateur en liste d’attente doit payer pour confirmer sa réservation."
        )

    messages.success(request, "Réservation annulée avec succès.")
    return redirect('my_registrations')

@login_required
def cancel_waitlist(request, id):
    if request.method != "POST":
        return HttpResponseForbidden("Méthode non autorisée")

    waitlist_entry = get_object_or_404(
        Waitlist,
        id=id,
        user=request.user,
        status__in=['waiting', 'notified']
    )

    waitlist_entry.status = 'cancelled'
    waitlist_entry.save(update_fields=['status'])

    messages.success(request, "Vous avez quitté la liste d’attente.")
    return redirect('my_registrations')