from django.contrib import admin
from allauth.account.decorators import secure_admin_login
from .models import Event, Ticket, Registration, Review, Purchase


admin.autodiscover()
admin.site.login = secure_admin_login(admin.site.login)


# Register your models here.
@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "created_by", "event_type", "status", "date")
    search_fields = ("title", "description")
    list_filter = ("date", "event_type", "status")


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("event", "price", "quantity")


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ("user", "event", "registered_at")
    search_fields = ("user__username", "event__title")


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("user", "event", "rating", "created_at")
    search_fields = ("user__username", "event__title")


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ("ticket", "user", "purchased_at")
    search_fields = ("user",)
    list_filter = ("purchased_at",)
