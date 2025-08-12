from rest_framework import serializers
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from Resturant.models import Table_Reservation, Table
from datetime import datetime


class Table_Reservation_Serializer(serializers.ModelSerializer):
    class Meta:
        model = Table_Reservation
        fields = "__all__"

    def validate(self, data):
        instance = self.instance
        user = self.context['request'].user

        # Ensure only the owner can update their reservation
        if instance and instance.user != user:
            raise ValidationError("You don't have permission to update this reservation.")

        # Validate party size does not exceed table seats
        if 'table' in data and 'number_of_party' in data:
            table = data['table']
            number_of_party = data['number_of_party']
            if table.seats < number_of_party:
                raise ValidationError("The party size exceeds the seats available at the reserved table.")

        # Validate reservation datetime logic
        if 'reservation_start' in data and 'reservation_end' in data:
            reservation_start = data['reservation_start']
            reservation_end = data['reservation_end']
            now = timezone.now()

            # Make sure reservation times are timezone-aware or naive consistently
            if reservation_start.tzinfo is None:
                reservation_start = timezone.make_aware(reservation_start)
            if reservation_end.tzinfo is None:
                reservation_end = timezone.make_aware(reservation_end)

            if reservation_start >= reservation_end:
                raise ValidationError("Reservation start must be before reservation end.")
            if reservation_start < now:
                raise ValidationError("Reservation start must be in the future.")
            # Restrict reservation hours between 8 and 23
            if not (8 <= reservation_start.hour <= 23):
                raise ValidationError("Reservations can only be made between 08:00 and 23:00 hours.")

        # Check for overlapping reservations on the same table
        if 'table' in data and 'reservation_start' in data and 'reservation_end' in data:
            table = data['table']
            reservation_start = data['reservation_start']
            reservation_end = data['reservation_end']

            overlapping_reservations = Table_Reservation.objects.filter(
                table=table,
                reservation_start__lt=reservation_end,
                reservation_end__gt=reservation_start,
            )
            if instance:
                overlapping_reservations = overlapping_reservations.exclude(id=instance.id)

            if overlapping_reservations.exists():
                raise ValidationError("The table is already reserved for the specified date and time range.")

        return data


class TableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Table
        fields = "__all__"
