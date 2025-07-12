from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from events.models import Event, Review
from events.forms import ReviewForm
from django_htmx.http import HttpResponseClientRefresh


@login_required
def review_create(request, pk):
    event = get_object_or_404(Event, id=pk)
    review_form = ReviewForm(request.POST)

    if request.method == "POST":
        if review_form.is_valid():
            review = review_form.save(commit=False)
            review.user = request.user
            review.event = event
            review.save()
            messages.success(request, "Review was submitted.")
            return render(request, "partials/_review.html", {"review": review}, status=201)

    return render(
        request, "partials/_review_form.html", {"review_form": review_form, "event": event}
    )


@login_required
def review_delete(request, pk):
    review = get_object_or_404(Review, pk=pk, user=request.user)

    if request.method == "DELETE":
        review.delete()
        messages.success(request, "Review was deleted.")

        return HttpResponseClientRefresh()

    return render(request, "modals/delete_modal.html", {"object": review})
