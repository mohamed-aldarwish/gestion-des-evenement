from django.db import models
from django.contrib.auth.models import User
from events.models import Event

import uuid
import qrcode

from io import BytesIO
from django.core.files import File




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

    quantity = models.PositiveIntegerField(
        default=1
    )

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

    booked_at = models.DateTimeField(
        auto_now_add=True
    )

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

    def save(self, *args, **kwargs):

        qr_data = f"""
        EVENT TICKET

        Ticket ID: {self.ticket_code}

        User: {self.user.username}

        Event: {self.event.title}

        Date: {self.event.event_date}

        Time: {self.event.event_time}

        Location: {self.event.location}

        Quantity: {self.quantity}

        Status: {self.status}
        """

        qr_image = qrcode.make(qr_data)

        qr_offset = BytesIO()
        qr_image.save(qr_offset, format='PNG')

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