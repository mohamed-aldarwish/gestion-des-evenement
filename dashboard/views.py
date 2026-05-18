import json

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponseForbidden
from django.db.models import Sum
from django.db.models.functions import ExtractMonth
from django.utils import timezone
from tickets.models import Ticket
from events.models import Event, Waitlist

@login_required
def dashboard_home(request):
    current_year = timezone.now().year

    user_tickets = (
        Ticket.objects.filter(user=request.user, status='active', payment_status='paid')
        .select_related('event')
        .order_by('-booked_at')
    )

    tickets_stats = (
        user_tickets.filter(booked_at__year=current_year)
        .annotate(month=ExtractMonth('booked_at'))
        .values('month')
        .annotate(total=Sum('quantity'))
        .order_by('month')
    )

    data_points = [0] * 12
    for entry in tickets_stats:
        if entry['month']:
            data_points[entry['month'] - 1] = entry['total'] or 0

    total_tickets_user = user_tickets.aggregate(
        total=Sum('quantity')
    )['total'] or 0

    context = {
        'total_events': Event.objects.filter(status='published').count(),
        'published_events': Event.objects.filter(status='published').count(),
        'total_tickets': total_tickets_user,

        'recent_events': Event.objects.filter(status='published').select_related('organizer').order_by('-created_at')[:5],
        'recent_tickets': user_tickets[:5],

        'chart_data': json.dumps(data_points),
    }

    return render(request, 'dashboard/dashboard.html', context)


@login_required
def my_tickets(request):
    tickets = (
        Ticket.objects.filter(
            user=request.user,
            status='active',
            payment_status='paid'
        )
        .select_related('event')
        .order_by('-booked_at')
    )

    return render(request, 'dashboard/my_tickets.html', {'tickets': tickets})


@login_required
def admin_dashboard(request):

    if not request.user.is_superuser:
        return HttpResponseForbidden(
            "Accès refusé. Vous devez être administrateur."
        )

    active_tickets = Ticket.objects.filter(
        status='active',
        payment_status='paid'
    ).select_related('event', 'user')

    total_tickets_admin = active_tickets.aggregate(
        total=Sum('quantity')
    )['total'] or 0

    context = {
        'total_users': User.objects.count(),
        'total_events': Event.objects.count(),
        'published_events': Event.objects.filter(status='published').count(),
        'total_tickets': total_tickets_admin,
        'recent_events': Event.objects.select_related('organizer').order_by('-created_at')[:5],
        'recent_tickets': active_tickets.order_by('-booked_at')[:5],
    }

    return render(
        request,
        'dashboard/admin_dashboard.html',
        context
    )




@login_required
def organizer_dashboard(request):

    if not hasattr(request.user, 'profile') or request.user.profile.role != 'organizer':
        return HttpResponseForbidden(
            "Accès refusé. Réservé aux organisateurs."
        )

    my_events = Event.objects.filter(
    organizer=request.user,
    status='published'
).order_by('-created_at')

    draft_events_list = Event.objects.filter(
    organizer=request.user,
    status='draft'
).order_by('-created_at')
    
    my_tickets = (
        Ticket.objects.filter(
            event__organizer=request.user,
            status='active',
            payment_status='paid'
        )
        .select_related('event', 'user')
    )

    waitlist_entries = (
        Waitlist.objects.filter(
            event__organizer=request.user,
            status='waiting'
        )
        .select_related('event', 'user')
    )

    total_tickets_organizer = my_tickets.aggregate(
        total=Sum('quantity')
    )['total'] or 0

    total_waitlist = waitlist_entries.count()

    total_revenue = my_tickets.filter(
        payment_status='paid'
    ).aggregate(
        total=Sum('amount')
    )['total'] or 0

    top_events = (
        my_events.annotate(
            revenue=Sum('tickets__amount')
        )
        .order_by('-revenue')[:5]
    )

    revenue_by_month = (
        my_tickets.filter(
            payment_status='paid',
            booked_at__year=timezone.now().year
        )
        .annotate(month=ExtractMonth('booked_at'))
        .values('month')
        .annotate(total=Sum('amount'))
        .order_by('month')
    )

    revenue_chart = [0] * 12

    for item in revenue_by_month:
        if item['month']:
            revenue_chart[item['month'] - 1] = float(item['total'] or 0)

    context = {

        'total_revenue': total_revenue,
        'top_events': top_events,
        'revenue_chart_data': json.dumps(revenue_chart),
        
        'total_events': my_events.count(),
        'my_events': my_events,
        'draft_events_list': draft_events_list,
        'published_events': my_events.filter(
            status='published'
        ).count(),

        'draft_events': draft_events_list.count(),

        'total_tickets': total_tickets_organizer,

        'total_waitlist': total_waitlist,

        'recent_events': my_events.order_by(
            '-created_at'
        )[:5],

        'recent_tickets': my_tickets.order_by(
            '-booked_at'
        )[:5],

        'waitlist_entries': waitlist_entries[:5],

        'my_events': my_events,
        'my_tickets': my_tickets,
    }

    return render(
        request,
        'dashboard/organizer_dashboard.html',
        context
    )

@login_required
def admin_events(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Access denied")

    search = request.GET.get('search', '')
    status = request.GET.get('status', '')

    events = Event.objects.select_related('organizer').order_by('-created_at')

    if search:
        events = events.filter(title__icontains=search)

    if status:
        events = events.filter(status=status)

    return render(request, 'dashboard/admin_events.html', {
        'events': events,
        'search': search,
        'status': status,
    })

@login_required
def admin_users(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Access denied")

    search = request.GET.get('search', '')
    role = request.GET.get('role', '')

    users = User.objects.all().order_by('-date_joined')

    if search:
        users = users.filter(username__icontains=search)

    if role == 'admin':
        users = users.filter(is_superuser=True)

    elif role == 'organizer':
        users = users.filter(profile__role='organizer')

    elif role == 'participant':
        users = users.filter(profile__role='user', is_superuser=False)

    return render(request, 'dashboard/admin_users.html', {
        'users': users,
        'search': search,
        'role': role,
    })

@login_required
def admin_tickets(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Access denied")

    tickets = Ticket.objects.select_related(
        'user',
        'event'
    ).order_by('-booked_at')

    return render(request, 'dashboard/admin_tickets.html', {
        'tickets': tickets
    })


@login_required
def admin_analytics(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Access denied")

    current_year = timezone.now().year

    tickets_by_month = (
        Ticket.objects.filter(status='active', payment_status='paid', booked_at__year=current_year)
        .annotate(month=ExtractMonth('booked_at'))
        .values('month')
        .annotate(total=Sum('quantity'))
        .order_by('month')
    )

    ticket_data = [0] * 12
    for entry in tickets_by_month:
        if entry['month']:
            ticket_data[entry['month'] - 1] = entry['total'] or 0

    published_count = Event.objects.filter(status='published').count()
    draft_count = Event.objects.filter(status='draft').count()

    context = {
        'total_users': User.objects.count(),
        'total_events': Event.objects.count(),
        'published_events': published_count,
        'draft_events': draft_count,
        'total_tickets': Ticket.objects.filter(status='active', payment_status='paid').aggregate(total=Sum('quantity'))['total'] or 0,

        'ticket_chart_data': json.dumps(ticket_data),
        'event_status_data': json.dumps([published_count, draft_count]),
    }

    return render(request, 'dashboard/admin_analytics.html', context)


@login_required
def admin_settings(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Access denied")

    return render(request, 'dashboard/admin_settings.html')
