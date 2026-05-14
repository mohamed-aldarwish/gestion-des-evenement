from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_home, name='dashboard_home'),

    path('organizer/', views.organizer_dashboard, name='organizer_dashboard'),

    path('admin/', views.admin_dashboard, name='admin_dashboard'),

    path('admin/events/', views.admin_events, name='admin_events'),

    path('admin/users/', views.admin_users, name='admin_users'),

    path('admin/tickets/', views.admin_tickets, name='admin_tickets'),

    path('admin/analytics/', views.admin_analytics, name='admin_analytics'),

    path('admin/settings/', views.admin_settings, name='admin_settings'),

    path('my-tickets/', views.my_tickets, name='my_tickets'),
]