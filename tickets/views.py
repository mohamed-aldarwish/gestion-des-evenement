import stripe
import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from accounts.permissions import can_reserve_events
from events.models import Event, Waitlist

from .models import Ticket
from .services import (
    NoSeatsAvailableError,
    PaymentConfirmationError,
    PaymentMetadataError,
    PaymentNotSucceeded,
    WaitlistPriorityError,
    confirm_paid_ticket,
    user_can_start_payment,
)
from io import BytesIO

import qrcode

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader


stripe.api_key = settings.STRIPE_SECRET_KEY
logger = logging.getLogger(__name__)


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
    event = get_object_or_404(Event, id=event_id, status='published')

    if not can_reserve_events(request.user):
        messages.error(request, "Organizer and admin accounts cannot reserve tickets.")
        return redirect('event_detail', id=event.id)

    can_pay, reason = user_can_start_payment(request.user, event)
    if not can_pay:
        messages.error(request, reason)
        return redirect('event_detail', id=event.id)

    waitlist_entry = Waitlist.objects.filter(
        user=request.user,
        event=event,
        status='notified'
    ).first()

    return render(request, 'tickets/payment_page.html', {
        'event': event,
        'waitlist_entry': waitlist_entry,
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
        'amount': event.price,
    })


@login_required
@require_POST
def create_payment_intent(request, event_id):
    event = get_object_or_404(Event, id=event_id, status='published')

    if not can_reserve_events(request.user):
        return JsonResponse({
            'error': 'Organizer and admin accounts cannot reserve tickets.'
        }, status=403)

    if event.price <= 0:
        return JsonResponse({
            'error': 'This event does not have a valid paid ticket price.'
        }, status=400)

    can_pay, reason = user_can_start_payment(request.user, event)
    if not can_pay:
        return JsonResponse({'error': reason}, status=403)

    waitlist_entry = Waitlist.objects.filter(
        user=request.user,
        event=event,
        status='notified'
    ).first()

    intent = stripe.PaymentIntent.create(
        amount=int(event.price * 100),
        currency='usd',
        metadata={
            'event_id': str(event.id),
            'user_id': str(request.user.id),
            'waitlist_id': str(waitlist_entry.id) if waitlist_entry else '',
        },
    )

    return JsonResponse({
        'clientSecret': intent.client_secret
    })


@login_required
def payment_success(request, event_id):
    event = get_object_or_404(Event, id=event_id, status='published')

    payment_intent_id = request.GET.get('payment_intent')

    if not payment_intent_id:
        client_secret = request.GET.get('payment_intent_client_secret')
        if client_secret:
            payment_intent_id = client_secret.split('_secret_')[0]

    if not can_reserve_events(request.user):
        messages.error(request, "Organizer and admin accounts cannot reserve tickets.")
        return redirect('event_detail', id=event.id)

    if not payment_intent_id:
        messages.error(request, "Payment could not be verified.")
        return redirect('event_detail', id=event.id)

    try:
        payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)

        ticket, created = confirm_paid_ticket(
            payment_intent,
            request_user=request.user
        )

    except PaymentNotSucceeded:
        messages.error(request, "Payment was not completed.")
        return redirect('tickets:payment_cancel')

    except (PaymentMetadataError, WaitlistPriorityError, NoSeatsAvailableError) as exc:
        messages.error(request, str(exc))
        return redirect('event_detail', id=event.id)

    except PaymentConfirmationError:
        messages.error(request, "Payment confirmation failed.")
        return redirect('event_detail', id=event.id)

    except Exception as exc:
        logger.exception("Stripe payment confirmation failed: %s", exc)
        messages.error(request, "Payment could not be verified.")
        return redirect('event_detail', id=event.id)

    if created:
        messages.success(request, "Payment successful. Your ticket is confirmed.")
    else:
        messages.info(request, "This payment has already been confirmed.")

    return redirect('tickets:ticket_detail', id=ticket.id)


@login_required
def payment_cancel(request):
    messages.warning(request, "Payment cancelled. No ticket was created.")
    return render(request, 'tickets/payment_cancel.html')


@csrf_exempt
@require_POST
def stripe_webhook(request):
    if not settings.STRIPE_WEBHOOK_SECRET:
        return HttpResponse("Stripe webhook secret is not configured.", status=503)

    payload = request.body
    signature = request.headers.get('Stripe-Signature')

    try:
        stripe_event = stripe.Webhook.construct_event(
            payload,
            signature,
            settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    if stripe_event['type'] == 'payment_intent.succeeded':
        payment_intent = stripe_event['data']['object']
        try:
            confirm_paid_ticket(payment_intent)
        except PaymentConfirmationError as exc:
            logger.exception("Stripe webhook confirmation failed: %s", exc)

    return HttpResponse(status=200)


def ticket_pdf_by_code(request, ticket_code):
    ticket = get_object_or_404(
        Ticket.objects.select_related('event', 'user'),
        ticket_code=ticket_code
    )

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = (
        f'inline; filename="ticket_{ticket.id}.pdf"'
    )

    pdf = canvas.Canvas(response, pagesize=A4)

    width, height = A4

    # =========================
    # Background
    # =========================
    pdf.setFillColorRGB(0.07, 0.07, 0.09)
    pdf.rect(0, 0, width, height, fill=1)

    # =========================
    # Main Card
    # =========================
    card_x = 2 * cm
    card_y = 4 * cm
    card_width = width - 4 * cm
    card_height = height - 8 * cm

    pdf.setFillColorRGB(1, 1, 1)
    pdf.roundRect(
        card_x,
        card_y,
        card_width,
        card_height,
        18,
        fill=1
    )

    # =========================
    # Header
    # =========================
    pdf.setFillColorRGB(0.1, 0.1, 0.12)

    pdf.roundRect(
        card_x,
        height - 7 * cm,
        card_width,
        3 * cm,
        18,
        fill=1
    )

    pdf.setFillColorRGB(1, 0.84, 0)

    pdf.setFont("Helvetica-Bold", 28)

    pdf.drawString(
        3 * cm,
        height - 5.3 * cm,
        "EventFiY Ticket"
    )

    # =========================
    # Event Title
    # =========================
    pdf.setFillColorRGB(0.15, 0.15, 0.15)

    pdf.setFont("Helvetica-Bold", 18)

    pdf.drawString(
        3 * cm,
        height - 9 * cm,
        ticket.event.title
    )

    # =========================
    # Information
    # =========================
    pdf.setFont("Helvetica", 12)

    y = height - 11 * cm

    line_space = 1 * cm

    info = [
        ("Ticket ID", ticket.id),
        ("Ticket Code", str(ticket.ticket_code)),
        ("Location", ticket.event.location),
        ("Date", str(ticket.event.event_date)),
        ("Time", str(ticket.event.event_time)),
        ("User", ticket.user.username),
        ("Email", ticket.user.email),
        ("Quantity", ticket.quantity),
        ("Status", ticket.status.upper()),
    ]

    for label, value in info:

        pdf.setFillColorRGB(0.3, 0.3, 0.3)

        pdf.setFont("Helvetica-Bold", 12)

        pdf.drawString(
            3 * cm,
            y,
            f"{label} :"
        )

        pdf.setFillColorRGB(0.1, 0.1, 0.1)

        pdf.setFont("Helvetica", 12)

        pdf.drawString(
            7 * cm,
            y,
            str(value)
        )

        y -= line_space

    # =========================
    # QR Code
    # =========================
    if ticket.qr_code:

        qr_size = 5 * cm

        pdf.drawImage(
            ticket.qr_code.path,
            width - 9 * cm,
            5 * cm,
            qr_size,
            qr_size
        )

    # =========================
    # Footer
    # =========================
    pdf.setFillColorRGB(0.5, 0.5, 0.5)

    pdf.setFont("Helvetica-Oblique", 10)

    pdf.drawCentredString(
        width / 2,
        2 * cm,
        "Generated securely by EventFiY"
    )

    pdf.showPage()
    pdf.save()

    return response