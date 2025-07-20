"""
URL configuration for Eventio project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.urls import path
from django.views.generic import TemplateView
from . import views

urlpatterns = [
    path("", views.event.event_list, name="event_list"),
    path("about/", TemplateView.as_view(template_name="about.html"), name="about"),
    path("contact/", views.event.ContactFormView.as_view(), name="contact"),
    path("thanks/", TemplateView.as_view(template_name="thanks.html"), name="thanks"),
    path("accounts/", views.account.account_detail, name="account_detail"),
    path("accounts/delete/", views.account.account_delete, name="account_delete"),
    path("event/", views.event.event_create, name="event_create"),
    path("event/<uuid:pk>/", views.event.event_detail, name="event_detail"),
    path("event/<uuid:pk>/edit/", views.event.event_update, name="event_update"),
    path("event/<uuid:pk>/delete/", views.event.event_delete, name="event_delete"),
    path("event/<uuid:pk>/register/", views.event.register_for_event, name="register_event"),
    path("event/<uuid:pk>/ticket/checkout/", views.event.buy_ticket, name="ticket_buy"),
    path("event/search/", views.event.event_search, name="event_search"),
    path("accounts/purchase/<int:pk>", views.event.purchase_detail, name="purchase_detail"),
    path("event/<uuid:pk>/review/", views.review.review_create, name="review_create"),
    path(
        "review/<int:pk>/delete/",
        views.review.review_delete,
        name="review_delete",
    ),
    path(
        "event/<uuid:pk>/ticket/checkout/success/",
        views.event.payment_success,
        name="ticket_payment_success",
    ),
]
