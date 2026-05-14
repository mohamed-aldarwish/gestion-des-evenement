from django.urls import path
from . import views

urlpatterns = [
    path('event/<int:event_id>/register/', views.register_event, name='register_event'),
    path('my-registrations/', views.my_registrations, name='my_registrations'),
    path('registration/<int:id>/cancel/', views.cancel_registration, name='cancel_registration'),
    path(
    'waitlist/<int:id>/cancel/',
    views.cancel_waitlist,
    name='cancel_waitlist'
),
]