from django.http import Http404
from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from allauth.account.decorators import reauthentication_required


def paginate_queryset(request, queryset, page_param="page", per_page=4):
    paginator = Paginator(queryset, per_page)
    page_number = request.GET.get(page_param)
    return paginator.get_page(page_number)


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
        request,
        "account.html",
        {"events": events, "registers": registers, "purchases": purchases},
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
