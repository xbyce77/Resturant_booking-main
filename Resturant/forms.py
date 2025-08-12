from django import forms
from django.forms import modelformset_factory
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Table_Reservation, TableOrder, TableOrderItem, Menu

# ✅ Form for the main table order
class TableOrderForm(forms.ModelForm):
    class Meta:
        model = TableOrder
        fields = ['reservation']

# ✅ Form for individual order items (menu + quantity)
class TableOrderItemForm(forms.ModelForm):
    class Meta:
        model = TableOrderItem
        fields = ['menu_item', 'quantity']
        widgets = {
            'menu_item': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'min': '1', 'class': 'form-control'})
        }

# ✅ FormSet to manage multiple items in one order
TableOrderItemFormSet = modelformset_factory(
    TableOrderItem,
    form=TableOrderItemForm,
    extra=1,
    can_delete=True
)

# ✅ Custom user registration form
class CustomRegistrationForm(UserCreationForm):
    phone_number = forms.CharField(max_length=10)
    address = forms.CharField(max_length=255)

    class Meta:
        model = User
        fields = (
            'first_name', 'last_name', 'username',
            'email', 'password1', 'password2',
            'phone_number', 'address'
        )

# ✅ Form for making a table reservation
from django.utils import timezone
from django import forms
from datetime import timedelta

class Table_ReservationForm(forms.ModelForm):
    reservation_start = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        input_formats=['%Y-%m-%dT%H:%M'],
    )
    reservation_end = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        input_formats=['%Y-%m-%dT%H:%M'],
    )

    class Meta:
        model = Table_Reservation
        fields = ('table', 'number_of_party', 'reservation_start', 'reservation_end', 'special_order')

    def clean(self):
        cleaned_data = super().clean()
        reservation_start = cleaned_data.get('reservation_start')
        reservation_end = cleaned_data.get('reservation_end')
        table = cleaned_data.get('table')

        if not reservation_start or not reservation_end or not table:
            return cleaned_data

        now = timezone.now()

        if reservation_start < now:
            raise forms.ValidationError("Reservation can't be made in the past.")
        if reservation_start.weekday() == 5:  # Saturday closed
            raise forms.ValidationError("Reservations cannot be made on Saturdays.")
        if not (8 <= reservation_start.hour < 23):
            raise forms.ValidationError("Reservations are allowed only between 08:00 and 23:00.")

        if reservation_end <= reservation_start:
            raise forms.ValidationError("Reservation end must be after the start time.")
        if reservation_end.weekday() == 5:
            raise forms.ValidationError("Restaurant is closed on Saturdays.")
        if not (8 <= reservation_end.hour < 23):
            raise forms.ValidationError("Reservations are allowed only between 08:00 and 23:00.")

        # Check if party size fits table seats
        if cleaned_data.get('number_of_party') > table.seats:
            raise forms.ValidationError(f"The party size exceeds the seats available at the table ({table.seats}).")

        # Check if the table is already booked for the requested time slot
        overlapping_reservations = Table_Reservation.objects.filter(
            table=table,
            reservation_start__lt=reservation_end,
            reservation_end__gt=reservation_start,
        )
        if self.instance.pk:
            overlapping_reservations = overlapping_reservations.exclude(pk=self.instance.pk)

        if overlapping_reservations.exists():
            raise forms.ValidationError(f"The table '{table.name}' is already booked during this time. Please choose a different table or time.")

        return cleaned_data


# ✅ Form to search menu items
class MenuSearchForm(forms.Form):
    query = forms.CharField(max_length=255, required=False, label="Search menu")