import logging
from django.http import Http404, HttpResponse
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.views.decorators.http import require_POST
from .models import Event, Registration, Ticket, Purchase, Review
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.db.models import Count
from .forms import EventForm, TicketForm, BuyTicketForm, ReviewForm
from allauth.account.decorators import reauthentication_required


def paginate_queryset(request, queryset, page_param="page", per_page=4):
    paginator = Paginator(queryset, per_page)
    page_number = request.GET.get(page_param)
    return paginator.get_page(page_number)


def event_list(request):
    events = Event.objects.filter(status="approved").select_related("ticket")
    popular = events.annotate(num_registers=Count("registrations")).order_by("-num_registers")[:4]
    recent_list = events.exclude(id__in=popular.values_list("id", flat=True))

    recent = paginate_queryset(request, recent_list)

    if request.htmx:
        return render(request, "partials/_recent_events.html", {"recent": recent})

    context = {"events": events, "popular": popular, "recent": recent}
    return render(request, "event_list.html", context)


def event_detail(request, pk):
    user = request.user
    event = get_object_or_404(Event.objects.select_related("created_by"), pk=pk)
    reviews = paginate_queryset(request, event.reviews.all(), per_page=4)

    if request.htmx:
        return render(
            request,
            "partials/_reviews.html",
            {"event": event, "reviews": reviews},
        )

    if event.is_paid and not event.status == "approved" and not event.is_allowed_to_view(user):
        raise Http404()

    has_reviewed = False
    has_joined = False

    if user.is_authenticated:
        has_reviewed = Review.objects.filter(user=user, event=event).exists()

        if event.is_paid:
            has_joined = Purchase.objects.filter(user=user, ticket__event=event).exists()
        else:
            has_joined = Registration.objects.filter(event=event, user=user).exists()

    context = {
        "event": event,
        "has_joined": has_joined,
        "has_reviewed": has_reviewed,
        "review_form": ReviewForm(),
        "reviews": reviews,
    }

    return render(request, "event_detail.html", context)


@login_required
def event_create(request, ticket_form=None):
    if request.htmx:
        event_type = request.GET.get("event_type")
        if event_type == "paid":
            ticket_form = TicketForm()
            return render(request, "partials/_ticket_form.html", {"ticket_form": ticket_form})

        return HttpResponse("")

    if request.method == "POST":
        event_form = EventForm(request.POST, request.FILES)
        ticket_form = TicketForm(request.POST)

        if event_form.is_valid() and (
            event_form.cleaned_data["event_type"] == "free" or ticket_form.is_valid()
        ):
            event = event_form.save(commit=False)
            event.created_by = request.user
            if event.is_free:
                event.status = "approved"
                event.save()
            else:
                event.status = "pending"
                event.save()
                ticket = ticket_form.save(commit=False)
                ticket.event = event
                ticket.save()

            messages.success(request, "Event was created successfully.")
            return redirect("event_detail", pk=event.pk)
    else:
        event_form = EventForm()

    context = {"form": event_form, "ticket_form": ticket_form}

    return render(request, "event_form.html", context)


@login_required
def event_update(request, pk, ticket_form=None):
    user = request.user
    event = get_object_or_404(Event.objects.select_related("ticket"), pk=pk, created_by=user)

    if request.htmx:
        event_type = request.GET.get("event_type", event.event_type)
        if event_type == "paid":
            ticket = event.ticket if event.is_paid else None
            ticket_form = TicketForm(instance=ticket)

            return render(request, "partials/_ticket_form.html", {"ticket_form": ticket_form})

        return HttpResponse("")

    if request.method == "POST":
        event_form = EventForm(request.POST, request.FILES, instance=event)
        ticket_form = TicketForm(request.POST)
        if event_form.is_valid():
            updated_event = event_form.save(commit=False)

            if updated_event.is_free:
                updated_event.save()
                messages.success(request, "Event was updated.")
                return redirect("event_detail", pk=pk)
            else:
                try:
                    ticket_form = TicketForm(request.POST, instance=event.ticket)
                except ObjectDoesNotExist:
                    pass

                if ticket_form.is_valid():
                    updated_event.save()
                    ticket = ticket_form.save(commit=False)
                    ticket.event = updated_event
                    ticket.save()
                    messages.success(request, "Event was updated.")
                    return redirect("event_detail", pk=pk)
    else:
        event_form = EventForm(instance=event)
        if event.is_paid:
            ticket_form = TicketForm(instance=event.ticket)

    context = {"event": event, "form": event_form, "ticket_form": ticket_form}

    return render(request, "event_form.html", context)


@login_required
def event_delete(request, pk):
    event = get_object_or_404(Event, pk=pk, created_by=request.user)
    if request.method == "POST":
        event.delete()
        messages.success(request, "Event was deleted.")
        return redirect("account_detail")
    return render(request, "event_delete.html", {"event": event})


@require_POST
@login_required
def register_for_event(request, pk):
    event = get_object_or_404(Event, pk=pk)
    register, created = Registration.objects.get_or_create(event=event, user=request.user)

    if created:
        messages.success(request, f"Registered for event {event.title}.")
    else:
        register.delete()
        messages.success(request, f"Unregistered from event {event.title}.")

    return redirect("event_detail", pk=event.pk)


@login_required
def buy_ticket(request, pk):
    user = request.user
    event = get_object_or_404(Event.objects.select_related("ticket"), pk=pk)
    form = BuyTicketForm(request.POST, ticket=event.ticket)

    if request.method == "POST":
        if form.is_valid():
            quantity = form.cleaned_data["ticket_quantity"]
            total_price = event.ticket.price * quantity

            try:
                purchase = Ticket.buy(user, event, quantity)
                messages.success(
                    request,
                    f"Purchased {quantity} tickets for {event.title} at ${total_price:.2f}.",
                )
                logging.info(
                    "Purchase successful: user "
                    f"{request.user} bought {quantity} tickets for {event} "
                    f"at ${total_price:.2f}."
                )
                return redirect("purchase_detail", pk=purchase.pk)
            except IntegrityError as e:
                logging.error(f"Ticket purchase failed: {e}")
                messages.error(
                    request, "Ticket purchase failed due to insufficient quantity or other issues."
                )

    return render(request, "ticket_buy.html", {"event": event, "form": form})


@login_required
def purchase_detail(request, pk):
    purchase = get_object_or_404(
        Purchase.objects.select_related("ticket__event", "user"), pk=pk, user=request.user
    )

    return render(request, "purchase_detail.html", {"purchase": purchase})


@login_required
def account_detail(request):
    user = request.user

    status = request.GET.get("status", "approved")
    purchase_page = request.GET.get("purchases")
    register_page = request.GET.get("registers")

    purchases = paginate_queryset(
        request,
        user.purchases.all().order_by("-purchased_at").select_related("user", "ticket__event"),
        page_param="purchases",
        per_page=5,
    )
    registers = paginate_queryset(
        request,
        user.registartions.all().order_by("-registered_at").select_related("event", "user"),
        page_param="registers",
        per_page=5,
    )

    if status in ["pending", "approved"]:
        events = paginate_queryset(
            request,
            user.events.filter(status=status).select_related("ticket"),
            page_param="events",
            per_page=5,
        )
    else:
        events = None

    if request.htmx:
        if purchase_page:
            return render(request, "partials/_account_purchases.html", {"purchases": purchases})
        elif register_page:
            return render(request, "partials/_account_registers.html", {"registers": registers})
        elif status:
            return render(
                request,
                "partials/_account_events.html",
                {"events": events},
            )
        return Http404()

    return render(
        request, "account.html", {"events": events, "registers": registers, "purchases": purchases}
    )


@login_required
@reauthentication_required
def account_delete(request):
    if request.POST:
        user = request.user
        logout(request)
        user.delete()
        messages.success(request, "Account successfully deleted")
        return redirect("event_list")

    return render(request, "account_delete.html")


def event_search(request):
    query = request.GET.get("q")
    if query:
        events = Event.objects.filter(status="approved", title__icontains=query).select_related(
            "ticket"
        )
        event_obj = paginate_queryset(request, events)
    else:
        event_obj = None

    if request.htmx:
        return render(request, "partials/_event_search.html", {"events": event_obj, "query": query})

    return render(request, "event_search.html", {"events": event_obj, "query": query})


@require_POST
@login_required
def review_create(request, pk):
    event = get_object_or_404(Event, id=pk)
    review_form = ReviewForm(request.POST)

    if review_form.is_valid():
        review = review_form.save(commit=False)
        review.user = request.user
        review.event = event
        review.save()
        messages.success(request, "Review was submitted.")
        return render(
            request,
            "partials/_review.html",
            {"review": review},
        )

    return redirect("event_detail", pk=pk)
