import logging
from django.conf import settings
from django.db.models import Avg, Count
from django.db.models.functions import Round
from django.http import Http404, HttpResponse
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.views.decorators.http import require_POST
import stripe
from events.models import Event, Registration, Ticket, Purchase, Review
from django.core.exceptions import ObjectDoesNotExist
from events.forms import EventForm, TicketForm, BuyTicketForm, ReviewForm
from events import payment

logger = logging.getLogger(__name__)


def paginate_queryset(request, queryset, page_param="page", per_page=4):
    paginator = Paginator(queryset, per_page)
    page_number = request.GET.get(page_param)
    return paginator.get_page(page_number)


def event_list(request):
    events = Event.objects.active().select_related("ticket")
    popular = events.popular()[:4]
    recent_list = events.recent().exclude(id__in=popular.values_list("id", flat=True))

    recent = paginate_queryset(request, recent_list)
    if request.htmx:
        return render(request, "partials/_recent_events.html", {"recent": recent})

    context = {"events": events[:4], "popular": popular, "recent": recent}
    return render(request, "event_list.html", context)


def event_detail(request, pk):
    user = request.user
    event = get_object_or_404(
        Event.objects.select_related("created_by").annotate(
            avg_rating=Round(Avg("reviews__rating"), 2), review_count=Count("reviews")
        ),
        pk=pk,
    )
    reviews = paginate_queryset(request, event.reviews.all().select_related("user"), per_page=4)

    if request.htmx:
        return render(
            request,
            "partials/_reviews.html",
            {"event": event, "reviews": reviews},
        )

    if event.is_paid and not event.is_active:
        if user.is_anonymous or not event.is_allowed_to_view(user):
            logger.warning(
                f"User {user.id if user.is_authenticated else 'anonymous'} tried to view event {event.id} that is paid and not active"
            )
            raise Http404()

    context = {
        "event": event,
        "has_joined": False,
        "has_reviewed": False,
        "review_form": ReviewForm(),
        "reviews": reviews,
    }

    if user.is_authenticated:
        context["has_reviewed"] = Review.objects.filter(user=user, event=event).exists()

        if event.is_paid:
            context["has_joined"] = Purchase.objects.filter(user=user, ticket__event=event).exists()
        else:
            context["has_joined"] = Registration.objects.filter(event=event, user=user).exists()

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

        if event_form.is_valid():
            event = event_form.save(commit=False)
            event.created_by = request.user
            if event.is_free:
                event.status = "approved"
                event.save()
                messages.success(request, "Event was created successfully.")
                return redirect("event_detail", pk=event.pk)

            if ticket_form.is_valid():
                ticket = ticket_form.save(commit=False)
                event.status = "pending"
                event.save()
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
                logger.info(f"Event {event.id} was updated by {request.user.id}")
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
        logger.info(f"Event {event.id} deleted by {request.user.id}")
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
    event = get_object_or_404(Event.objects.select_related("ticket"), pk=pk)
    form = BuyTicketForm(request.POST, ticket=event.ticket)

    if request.method == "POST":
        if form.is_valid():
            quantity = form.cleaned_data["ticket_quantity"]

            success_url = request.build_absolute_uri(
                reverse("ticket_payment_success", kwargs={"pk": event.pk})
            )

            cancel_url = request.build_absolute_uri(reverse("ticket_buy", kwargs={"pk": event.pk}))

            try:
                checkout_url = payment.start_checkout_session(
                    success_url=success_url,
                    cancel_url=cancel_url,
                    price=event.ticket.price_to_cents,
                    quantity=quantity,
                    product_data={
                        "name": f"{event.title} - Ticket",
                        "description": event.description,
                        "images": [event.get_banner_url()],
                    },
                )
                logger.info(
                    f"User {request.user.id} started payment on ticket {event.ticket.id} for {quantity} qty."
                )
                return redirect(checkout_url)
            except stripe.error.StripeError as e:
                logger.error(f"Stripe error: {e}")
                messages.error(
                    request,
                    "There was an error processing your payment. Please try again.",
                )

    return render(
        request,
        "ticket_buy.html",
        {"event": event, "form": form, "stripe_public_key": settings.STRIPE_API_PUBLIC},
    )


@login_required
def payment_success(request, pk):
    session_id = request.GET.get("session_id")

    checkout_session = payment.get_checkout_session(session_id)

    quantity = int(checkout_session.metadata.get("quantity", 1))

    try:
        event = Event.objects.get(pk=pk)
    except ObjectDoesNotExist:
        messages.error(request, "Event not found.")
        return redirect("event_list")

    purchase = Ticket.buy(request.user, event, quantity)
    messages.success(
        request,
        f"Purchased {quantity} tickets for {event.title}.",
    )
    logger.info(f"User {request.user.id} purchased successfully {quantity} tickets for {event}")
    return redirect("purchase_detail", pk=purchase.pk)


@login_required
def purchase_detail(request, pk):
    purchase = get_object_or_404(
        Purchase.objects.select_related("ticket__event", "user"),
        pk=pk,
        user_id=request.user.id,
    )

    return render(request, "purchase_detail.html", {"purchase": purchase})


def event_search(request):
    query = request.GET.get("q")
    if query:
        events = Event.objects.active().filter(title__icontains=query).select_related("ticket")
        event_obj = paginate_queryset(request, events)
    else:
        events = Event.objects.all().select_related("ticket")
        event_obj = paginate_queryset(request, events)

    if request.htmx:
        return render(
            request,
            "partials/_event_search.html",
            {"events": event_obj, "query": query},
        )

    return render(request, "event_search.html", {"events": event_obj, "query": query})
