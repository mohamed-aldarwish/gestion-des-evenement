from django.urls import path
from . import views
from tickets import views as ticket_views

urlpatterns = [
    path('', views.event_list, name='event_list'),
    path('create/', views.event_create, name='event_create'),
    path('<int:id>/', views.event_detail, name='event_detail'),
    path('<int:id>/edit/', views.event_update, name='event_update'),
    path('<int:id>/delete/', views.event_delete, name='event_delete'),
    path('<int:event_id>/book/', views.book_ticket, name='book_ticket'),
    path('<int:event_id>/waitlist/', views.join_waitlist, name='join_waitlist'),
    path('tickets/<int:ticket_id>/cancel/', views.cancel_ticket, name='cancel_ticket'),
    path('payment-success/<int:event_id>/', ticket_views.payment_success, name='event_payment_success'),
    path('payment-cancel/', ticket_views.payment_cancel, name='event_payment_cancel'),
]
