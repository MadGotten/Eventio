from django import forms
from django.core.validators import MaxValueValidator
from .models import Event, Ticket
from datetime import datetime


class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ("price", "quantity")


class EventForm(forms.ModelForm):
    banner = forms.ImageField(required=False, widget=forms.FileInput)
    event_type = forms.ChoiceField(
        choices=Event.EVENT_TYPE_CHOICES,
        widget=forms.Select(),
    )
    date = forms.DateTimeField(
        widget=forms.DateInput(format="%Y-%m-%dT%H:%M", attrs={"type": "datetime-local"}),
        initial=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        input_formats=["%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M"],
    )

    class Meta:
        model = Event
        fields = ("title", "description", "location", "date", "category", "banner", "event_type")


class BuyTicketForm(forms.Form):
    ticket_quantity = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={"value": 1, "x-model.number": "quantity"}),
    )

    def __init__(self, *args, **kwargs):
        ticket = kwargs.pop("ticket", None)
        super().__init__(*args, **kwargs)

        if ticket:
            self.fields["ticket_quantity"].validators.append(MaxValueValidator(ticket.quantity))
            self.fields["ticket_quantity"].widget.attrs["max"] = ticket.quantity
