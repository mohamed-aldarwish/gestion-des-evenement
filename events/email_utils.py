import logging

from django.conf import settings
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


logger = logging.getLogger(__name__)


def _send_sendgrid_message(message):
    if not settings.SENDGRID_API_KEY:
        return False

    try:
        SendGridAPIClient(settings.SENDGRID_API_KEY).send(message)
        return True
    except Exception as exc:
        logger.exception("SendGrid email failed: %s", exc)
        return False


def send_waitlist_available_email(user, event):
    if not user.email or not settings.SENDGRID_API_KEY:
        return False

    message = Mail(
        from_email=settings.DEFAULT_FROM_EMAIL,
        to_emails=user.email,
        subject=f"A seat is available - {event.title}",
        html_content=f"""
        <h2 style="color:#0f172a;">A seat is now available for this event</h2>

        <p>Hello <strong>{user.username}</strong>,</p>

        <p>
            A seat is now available for <strong>{event.title}</strong>.
            Please log in and complete payment to confirm your ticket.
        </p>

        <div style="background:#f8fafc; padding:20px; border-radius:12px; margin:20px 0;">
            <p><strong>Event:</strong> {event.title}</p>
            <p><strong>Date:</strong> {event.event_date}</p>
            <p><strong>Location:</strong> {event.location}</p>
        </div>

        <p>This invitation does not reserve your seat until payment succeeds.</p>

        <p>
            Best regards,<br>
            <strong>EventFiY Team</strong>
        </p>
        """
    )

    return _send_sendgrid_message(message)


def send_ticket_confirmed_email(user, ticket):
    if not user.email or not settings.SENDGRID_API_KEY:
        return False

    message = Mail(
        from_email=settings.DEFAULT_FROM_EMAIL,
        to_emails=user.email,
        subject=f"Reservation Confirmed - {ticket.event.title}",
        html_content=f"""
        <h2 style="color:#0f172a;">Reservation Confirmed</h2>

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

        <p>
            Best regards,<br>
            <strong>EventFiY Team</strong>
        </p>
        """
    )

    return _send_sendgrid_message(message)
