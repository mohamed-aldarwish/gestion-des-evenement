from django.db import models
from django.contrib.auth.models import User
from django.db.models import Sum


class Event(models.Model):

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('cancelled', 'Cancelled'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    event_date = models.DateField()
    event_time = models.TimeField()
    location = models.CharField(max_length=200)
    capacity = models.PositiveIntegerField()
    category = models.CharField(max_length=100, blank=True, null=True)
    image = models.ImageField(
        upload_to='event_images/',
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )

    organizer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='organized_events'
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def booked_seats(self):
        if hasattr(self, 'booked_seats_count'):
            return self.booked_seats_count or 0

        return self.tickets.filter(
            status='active',
            payment_status='paid'
        ).aggregate(
            total=Sum('quantity')
        ).get('total') or 0

    @property
    def remaining_seats(self):
        return self.capacity - self.booked_seats

    def __str__(self):
        return self.title


class Waitlist(models.Model):

    STATUS_CHOICES = [
        ('waiting', 'Waiting'),
        ('notified', 'Notified'),
        ('converted', 'Converted'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='waitlist_entries'
    )

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='waitlist_entries'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='waiting'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    notified_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['created_at']
        unique_together = ('user', 'event')

    def __str__(self):
        return f"{self.user.username} - {self.event.title} ({self.status})"
