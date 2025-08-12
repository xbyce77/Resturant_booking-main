from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User


# --------------------
# Profile Model
# --------------------
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=10)
    address = models.CharField(max_length=255)

    def __str__(self):
        return self.user.username


# --------------------
# Custom Validator
# --------------------
def validate_less_than_99(value):
    if value >= 99 or value <= 0:
        raise ValidationError(_('Value must be greater than 0 and less than 99.'))


# --------------------
# Table Model
# --------------------
class Table(models.Model):
    seats = models.IntegerField(validators=[validate_less_than_99])
    name = models.CharField(max_length=255)

    class Meta:
        ordering = ["seats"]

    def __str__(self):
        return f"{self.name} - seats: {self.seats}"


# --------------------
# Table Reservation Model
# (kept original table name so migrations won't break)
# --------------------
class Table_Reservation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    table = models.ForeignKey(Table, on_delete=models.CASCADE)
    number_of_party = models.IntegerField(validators=[validate_less_than_99])
    reservation_start = models.DateTimeField()
    reservation_end = models.DateTimeField()
    special_order = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["reservation_start"]
        db_table = "table_reservation"  # Keep old DB table name

    def __str__(self):
        start_date = self.reservation_start.strftime("%Y-%m-%d %H:%M")
        end_date = self.reservation_end.strftime("%Y-%m-%d %H:%M")
        return f"{start_date} → {end_date}"

    def clean(self):
        super().clean()
        # Check party size
        if self.table and self.number_of_party > self.table.seats:
            raise ValidationError(
                f"The party size ({self.number_of_party}) is greater than seats available in the table."
            )
        # Check overlapping reservations
        if self.table:
            existing_reservations = Table_Reservation.objects.filter(
                table=self.table,
                reservation_start__lt=self.reservation_end,
                reservation_end__gt=self.reservation_start,
            )
            if self.pk:
                existing_reservations = existing_reservations.exclude(pk=self.pk)
            if existing_reservations.exists():
                raise ValidationError(
                    "The table is already reserved for the specified date and time."
                )


# --------------------
# Category Model
# --------------------
class Category(models.Model):
    type = models.CharField(max_length=255, default='General')

    def __str__(self):
        return self.type


# --------------------
# Menu Model
# --------------------
class Menu(models.Model):
    item_name = models.CharField(max_length=255)
    item_price = models.FloatField()
    ingredients = models.TextField()
    images = models.FileField(upload_to="img/", blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)

    def __str__(self):
        return self.item_name

    def save(self, *args, **kwargs):
        self.item_price = round(self.item_price, 2)
        super().save(*args, **kwargs)


# --------------------
# Table Order Models
# --------------------
class TableOrder(models.Model):
    reservation = models.ForeignKey(
        Table_Reservation, on_delete=models.CASCADE, related_name='table_orders'
    )
    menu_items = models.ManyToManyField(Menu, through='TableOrderItem', related_name='table_orders')

    def __str__(self):
        return f"Order for {self.reservation}"


class TableOrderItem(models.Model):
    table_order = models.ForeignKey(TableOrder, on_delete=models.CASCADE, related_name='items')
    menu_item = models.ForeignKey(Menu, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.menu_item.item_name} x{self.quantity}"


# --------------------
# Cart Item Model
# --------------------
class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    menu_item = models.ForeignKey(Menu, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.menu_item.item_name} x{self.quantity}"
