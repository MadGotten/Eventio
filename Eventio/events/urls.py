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
from . import views

urlpatterns = [
    path("", views.event_list, name="event_list"),
    path("accounts/", views.account_detail, name="account_detail"),
    path("accounts/delete", views.account_delete, name="account_delete"),
    path("event/", views.event_create, name="event_create"),
    path("event/<uuid:pk>/", views.event_detail, name="event_detail"),
    path("event/<uuid:pk>/edit/", views.event_update, name="event_update"),
    path("event/<uuid:pk>/delete/", views.event_delete, name="event_delete"),
    path("event/<uuid:pk>/register/", views.register_for_event, name="register_event"),
    path("event/<uuid:pk>/buy_ticket/", views.buy_ticket, name="ticket_buy"),
    path("event/search/", views.event_search, name="event_search"),
    path("accounts/purchase/<int:pk>", views.purchase_detail, name="purchase_detail"),
    path("event/<uuid:pk>/review", views.review_create, name="review_create"),
]
