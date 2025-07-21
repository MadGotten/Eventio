from django.contrib import admin
from allauth.account.decorators import secure_admin_login
from events.models import Event, Ticket, Registration, Review, Purchase


admin.autodiscover()
admin.site.login = secure_admin_login(admin.site.login)


# Register your models here.
@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "created_by", "event_type", "status", "date")
    search_fields = ("title", "description")
    list_filter = ("date", "event_type", "status")
    readonly_fields = ("created_at", "updated_at")


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("event", "price", "quantity")


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ("user", "event")
    search_fields = ("user__username", "event__title")
    readonly_fields = ("registered_at",)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("user", "event", "rating", "created_at")
    search_fields = ("user__username", "event__title")


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ("ticket", "user", "event_name", "amount_paid")
    search_fields = ("user",)
    list_filter = ("purchased_at",)
    readonly_fields = ("purchased_at",)
