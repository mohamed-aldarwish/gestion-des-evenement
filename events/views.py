from urllib import request

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.http import Http404

from events.models import Event
from tickets.models import Ticket
from .forms import EventForm


def event_list(request):

    if request.user.is_authenticated and request.user.is_superuser:
        return redirect('admin_events')

    search = request.GET.get('search', '')
    category = request.GET.get('category', '')
    status = request.GET.get('status', '')

    if request.user.is_authenticated and request.user.profile.role == 'organizer':

        events = Event.objects.filter(
            organizer=request.user
        ).order_by('-created_at')

    else:

        events = Event.objects.filter(
            status='published'
        ).order_by('-created_at')

    if search:
        events = events.filter(title__icontains=search)

    if category:
        events = events.filter(category__icontains=category)

    if status:

        if request.user.is_authenticated and (
            request.user.is_superuser or
            request.user.profile.role == 'organizer'
        ):

            events = events.filter(status=status)

    return render(request, 'events/event_list.html', {
        'events': events,
        'search': search,
        'category': category,
        'status': status,
    })


def event_detail(request, id):
    event = get_object_or_404(Event, id=id)

    if event.status != 'published':
        if not request.user.is_authenticated:
            raise Http404

        if not request.user.is_superuser and event.organizer != request.user:
            raise Http404

    return render(request, 'events/event_detail.html', {
        'event': event
    })


@login_required
def event_create(request):
    if not request.user.is_staff and request.user.profile.role != 'organizer':
        return HttpResponseForbidden("Access denied")

    if request.method == 'POST':
        print('EVENT_CREATE POST token=', request.POST.get('csrfmiddlewaretoken'))
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

    if event.organizer != request.user and not request.user.is_superuser:
        return HttpResponseForbidden("Access denied")

    if request.method == 'POST':
        print('EVENT_UPDATE POST token=', request.POST.get('csrfmiddlewaretoken'))
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

    if event.organizer != request.user and not request.user.is_superuser:
        return HttpResponseForbidden("Access denied")

    if request.method == 'POST':
        print('EVENT_DELETE POST token=', request.POST.get('csrfmiddlewaretoken'))
        event.delete()
        return redirect('event_list')

    return render(request, 'events/event_confirm_delete.html', {'event': event})


@login_required
def book_ticket(request, event_id):
    event = get_object_or_404(Event, id=event_id, status='published')

    remaining = event.remaining_seats() if callable(event.remaining_seats) else event.remaining_seats

    if request.method == 'POST':
        try:
            quantity = int(request.POST.get('quantity', 1))
        except ValueError:
            return render(request, 'events/error.html', {
                'message': 'Invalid ticket quantity.'
            })

        if quantity <= 0:
            return render(request, 'events/error.html', {
                'message': 'Invalid ticket quantity.'
            })

        if quantity > remaining:
            return render(request, 'events/error.html', {
                'message': 'Not enough seats available.'
            })

        ticket = Ticket.objects.create(
            event=event,
            user=request.user,
            quantity=quantity,
            status='active'
        )

        print("TICKET CREATED:", ticket.id, ticket.user.username, ticket.quantity)

        return redirect('dashboard_home')

    return render(request, 'events/book_ticket.html', {
        'event': event,
        'remaining_seats': remaining
    })