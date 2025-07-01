from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from events.models import Event, Review
from events.forms import ReviewForm


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


@login_required
def review_delete(request, pk):
    review = get_object_or_404(Review, pk=pk, user=request.user)

    if request.method == "POST":
        review.delete()
        messages.success(request, "Review was deleted.")

        return redirect("event_detail", pk=review.event.id)

    return render(request, "modals/delete_modal.html", {"object": review})
