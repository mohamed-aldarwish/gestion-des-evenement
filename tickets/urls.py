from django.urls import path
from . import views

urlpatterns = [
    path('<int:id>/', views.ticket_detail, name='ticket_detail'),

    path(
        'payment/<int:event_id>/',
        views.payment_page,
        name='payment_page'
    ),

    path(
        'payment-intent/<int:event_id>/',
        views.create_payment_intent,
        name='create_payment_intent'
    ),

    path(
        'payment-success/<int:event_id>/',
        views.payment_success,
        name='payment_success'
    ),

    path(
        'payment-cancel/',
        views.payment_cancel,
        name='payment_cancel'
    ),
]