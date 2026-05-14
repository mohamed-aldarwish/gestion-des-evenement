from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Profile


def register_view(request):
    if request.user.is_authenticated:
        return redirect('event_list')

    if request.method == 'POST':
        print('REGISTER_VIEW POST token=', request.POST.get('csrfmiddlewaretoken'))
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


@login_required
def profile_view(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    return render(request, 'accounts/profile.html', {
        'profile': profile
    })