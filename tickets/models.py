from django.db import models
from django.contrib.auth.models import User
from django.db.models import Q
from django.conf import settings
from django.urls import reverse
from django.core.files import File

from events.models import Event

import uuid
import qrcode
from io import BytesIO


class Ticket(models.Model):

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='tickets'
    )

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='tickets'
    )

    quantity = models.PositiveIntegerField(default=1)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )

    payment_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('paid', 'Paid'),
            ('failed', 'Failed'),
        ],
        default='pending'
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    stripe_session_id = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    booked_at = models.DateTimeField(auto_now_add=True)

    ticket_code = models.UUIDField(
        default=uuid.uuid4,
        editable=False
    )

    qr_code = models.ImageField(
        upload_to='qr_codes/',
        blank=True,
        null=True
    )

    class Meta:
        ordering = ['-booked_at']
        constraints = [
            models.UniqueConstraint(
                fields=['stripe_session_id'],
                condition=Q(stripe_session_id__isnull=False),
                name='unique_paid_stripe_payment_reference'
            ),
            models.UniqueConstraint(
                fields=['user', 'event'],
                condition=Q(status='active', payment_status='paid'),
                name='unique_active_paid_ticket_per_user_event'
            ),
        ]

    def save(self, *args, **kwargs):
        if self.qr_code:
            super().save(*args, **kwargs)
            return

        pdf_url = (
            f"{settings.SITE_URL}"
            f"{reverse('tickets:ticket_pdf_by_code', args=[self.ticket_code])}"
        )

        qr_image = qrcode.make(pdf_url)

        qr_offset = BytesIO()
        qr_image.save(qr_offset, format='PNG')
        qr_offset.seek(0)

        file_name = f'ticket-{self.ticket_code}.png'

        self.qr_code.save(
            file_name,
            File(qr_offset),
            save=False
        )

        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.user.username} - "
            f"{self.event.title} "
            f"({self.quantity})"
        )