from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.http import Http404
from django.views.decorators.http import require_POST
from django.db.models import Q, Sum, Value
from django.db.models.functions import Coalesce

from accounts.permissions import can_manage_event, can_reserve_events, is_organizer
from events.models import Event, Waitlist
from events.services import join_event_waitlist
from tickets.models import Ticket
from tickets.services import cancel_paid_ticket
from .forms import EventForm


def event_queryset():
    return (
        Event.objects.select_related('organizer')
        .annotate(
            booked_seats_count=Coalesce(
                Sum(
                    'tickets__quantity',
                    filter=Q(
                        tickets__status='active',
                        tickets__payment_status='paid'
                    )
                ),
                Value(0)
            )
        )
    )


def event_list(request):

    if request.user.is_authenticated and request.user.is_superuser:
        return redirect('admin_events')

    search = request.GET.get('search', '')
    category = request.GET.get('category', '')
    status = request.GET.get('status', '')

    if is_organizer(request.user):

        events = event_queryset().filter(
            organizer=request.user
        ).order_by('-created_at')

    else:

        events = event_queryset().filter(
            status='published'
        ).order_by('-created_at')

    if search:
        events = events.filter(title__icontains=search)

    if category:
        events = events.filter(category__icontains=category)

    if status:

        if request.user.is_authenticated and (
            request.user.is_superuser or
            is_organizer(request.user)
        ):

            events = events.filter(status=status)

    return render(request, 'events/event_list.html', {
        'events': events,
        'search': search,
        'category': category,
        'status': status,
    })


def event_detail(request, id):
    event = get_object_or_404(event_queryset(), id=id)

    if event.status != 'published':
        if not request.user.is_authenticated:
            raise Http404

        if not can_manage_event(request.user, event):
            raise Http404

    user_ticket = None
    waitlist_entry = None

    if can_reserve_events(request.user):
        user_ticket = Ticket.objects.filter(
            user=request.user,
            event=event,
            status='active',
            payment_status='paid'
        ).first()
        waitlist_entry = Waitlist.objects.filter(
            user=request.user,
            event=event,
            status__in=['waiting', 'notified']
        ).first()

    return render(request, 'events/event_detail.html', {
        'event': event,
        'user_ticket': user_ticket,
        'waitlist_entry': waitlist_entry,
        'can_reserve': can_reserve_events(request.user),
    })


@login_required
def event_create(request):
    if not can_manage_event(request.user):
        return HttpResponseForbidden("Access denied")

    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.organizer = request.user
            event.save()
            return redirect('event_detail', id=event.id)

    else:
        form = EventForm()

    return render(request, 'events/event_form.html', {'form': form})


@login_required
def event_update(request, id):
    event = get_object_or_404(Event, id=id)

    if not can_manage_event(request.user, event):
        return HttpResponseForbidden("Access denied")

    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            form.save()
            return redirect('event_detail', id=event.id)

    else:
        form = EventForm(instance=event)

    return render(request, 'events/event_form.html', {
        'form': form,
        'event': event
    })


@login_required
def event_delete(request, id):
    event = get_object_or_404(Event, id=id)

    if not can_manage_event(request.user, event):
        return HttpResponseForbidden("Access denied")

    if request.method == 'POST':
        event.delete()
        return redirect('event_list')

    return render(request, 'events/event_confirm_delete.html', {'event': event})


@login_required
def book_ticket(request, event_id):
    event = get_object_or_404(Event, id=event_id, status='published')

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

    remaining = event.remaining_seats

    if request.method == 'POST':
        if remaining <= 0:
            waitlist_entry, created = join_event_waitlist(request.user, event)
            if created:
                messages.success(request, "You joined the waitlist. We will email you when a seat opens.")
            elif waitlist_entry.status in ['waiting', 'notified']:
                messages.info(request, "You are already on the waitlist for this event.")
            else:
                waitlist_entry.status = 'waiting'
                waitlist_entry.notified_at = None
                waitlist_entry.save(update_fields=['status', 'notified_at'])
                messages.success(request, "You rejoined the waitlist.")
            return redirect('event_detail', id=event.id)

        messages.info(request, "Complete payment to confirm your ticket.")
        return redirect('payment_page', event_id=event.id)

    return render(request, 'events/book_ticket.html', {
        'event': event,
        'remaining_seats': remaining
    })


@login_required
@require_POST
def join_waitlist(request, event_id):
    event = get_object_or_404(Event, id=event_id, status='published')

    if not can_reserve_events(request.user):
        messages.error(request, "Organizer and admin accounts cannot join waitlists.")
        return redirect('event_detail', id=event.id)

    if Ticket.objects.filter(
        user=request.user,
        event=event,
        status='active',
        payment_status='paid'
    ).exists():
        messages.info(request, "You already have a confirmed ticket for this event.")
        return redirect('event_detail', id=event.id)

    if event.remaining_seats > 0:
        messages.info(request, "Seats are available. Please complete payment to reserve.")
        return redirect('payment_page', event_id=event.id)

    waitlist_entry, created = join_event_waitlist(request.user, event)

    if created:
        messages.success(request, "You joined the waitlist. We will email you when a seat opens.")
    elif waitlist_entry.status in ['waiting', 'notified']:
        messages.info(request, "You are already on the waitlist for this event.")
    else:
        waitlist_entry.status = 'waiting'
        waitlist_entry.notified_at = None
        waitlist_entry.save(update_fields=['status', 'notified_at'])
        messages.success(request, "You rejoined the waitlist.")

    return redirect('event_detail', id=event.id)


@login_required
@require_POST
def cancel_ticket(request, ticket_id):
    ticket = get_object_or_404(
        Ticket.objects.select_related('event'),
        id=ticket_id,
        user=request.user,
        status='active',
        payment_status='paid'
    )

    _, notified_entry = cancel_paid_ticket(ticket)

    messages.success(request, "Your ticket was cancelled.")
    if notified_entry:
        messages.info(request, "The first waitlisted user has been notified.")
    return redirect('my_registrations')
