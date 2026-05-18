from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum

from events.models import Event
from tickets.models import Ticket
from .forms import ProfileUpdateForm, UserUpdateForm
from .models import Profile


def register_view(request):
    if request.user.is_authenticated:
        return redirect('event_list')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        phone = request.POST.get('phone', '').strip()

        if not username or not email or not password:
            return render(request, 'accounts/register.html', {
                'error': 'All required fields must be filled.'
            })

        if User.objects.filter(username=username).exists():
            return render(request, 'accounts/register.html', {
                'error': 'Username already exists.'
            })

        if User.objects.filter(email=email).exists():
            return render(request, 'accounts/register.html', {
                'error': 'Email already exists.'
            })

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        profile, created = Profile.objects.get_or_create(user=user)
        profile.phone = phone
        profile.role = 'user'
        profile.save()

        messages.success(request, 'Account created successfully. Please login.')
        return redirect('login')

    return render(request, 'accounts/register.html')


def login_view(request):
    if request.user.is_authenticated:
        profile, created = Profile.objects.get_or_create(
            user=request.user
        )

        if request.user.is_superuser:
            return redirect('admin_dashboard')

        return redirect('event_list')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)

            profile, created = Profile.objects.get_or_create(
                user=user
            )

            if user.is_superuser:
                return redirect('admin_dashboard')

            return redirect('event_list')

        return render(request, 'accounts/login.html', {
            'error': 'Invalid username or password.'
        })

    return render(request, 'accounts/login.html')


@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


def _delete_avatar_file(storage, file_name):
    if not storage or not file_name:
        return

    if storage.exists(file_name):
        storage.delete(file_name)


def _profile_stats(user):
    paid_tickets = Ticket.objects.filter(
        user=user,
        status='active',
        payment_status='paid',
    )
    organized_events = Event.objects.filter(organizer=user)

    stats = [
        {
            'label': 'Tickets',
            'value': paid_tickets.aggregate(total=Sum('quantity'))['total'] or 0,
            'icon': 'fa-ticket-alt',
        },
        {
            'label': 'Events Joined',
            'value': paid_tickets.values('event_id').distinct().count(),
            'icon': 'fa-calendar-check',
        },
    ]

    if user.is_superuser:
        stats.extend([
            {
                'label': 'Managed Events',
                'value': Event.objects.count(),
                'icon': 'fa-calendar-days',
            },
            {
                'label': 'Users',
                'value': User.objects.count(),
                'icon': 'fa-users',
            },
        ])
    elif getattr(user.profile, 'role', None) == 'organizer':
        stats.extend([
            {
                'label': 'My Events',
                'value': organized_events.count(),
                'icon': 'fa-calendar-days',
            },
            {
                'label': 'Published',
                'value': organized_events.filter(status='published').count(),
                'icon': 'fa-bullhorn',
            },
        ])

    return stats


def _profile_completion(user, profile):
    fields = [
        user.username,
        user.first_name,
        user.last_name,
        user.email,
        profile.phone,
        profile.avatar,
        profile.bio,
    ]
    completed = sum(1 for value in fields if bool(value))
    return round((completed / len(fields)) * 100)


@login_required
def profile_view(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    return render(request, 'accounts/profile.html', {
        'profile': profile,
        'stats': _profile_stats(request.user),
        'profile_completion': _profile_completion(request.user, profile),
        'full_name': request.user.get_full_name() or request.user.username,
    })


@login_required
def edit_profile_view(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    previous_avatar_name = profile.avatar.name if profile.avatar else ''
    previous_avatar_storage = profile.avatar.storage if profile.avatar else None

    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(
            request.POST,
            request.FILES,
            instance=profile,
        )

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()

            updated_profile = profile_form.save(commit=False)
            remove_avatar = profile_form.cleaned_data.get('remove_avatar')
            uploaded_avatar = request.FILES.get('avatar')

            if remove_avatar:
                _delete_avatar_file(previous_avatar_storage, previous_avatar_name)
                updated_profile.avatar = None
            elif uploaded_avatar and previous_avatar_name:
                _delete_avatar_file(previous_avatar_storage, previous_avatar_name)

            updated_profile.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('profile')

        messages.error(request, 'Please correct the highlighted fields.')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=profile)

    return render(request, 'accounts/edit_profile.html', {
        'profile': profile,
        'user_form': user_form,
        'profile_form': profile_form,
        'full_name': request.user.get_full_name() or request.user.username,
    })


@login_required
def change_password_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)

        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password changed successfully.')
            return redirect('profile')

        messages.error(request, 'Please correct the highlighted fields.')
    else:
        form = PasswordChangeForm(request.user)

    for field in form.fields.values():
        field.widget.attrs.update({'class': 'profile-input'})

    return render(request, 'accounts/change_password.html', {
        'form': form,
    })
