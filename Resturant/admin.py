from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Profile, Table, Table_Reservation,
    Category, Menu, TableOrder, TableOrderItem
)

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'address')
    search_fields = ('user__username', 'phone_number')


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ('name', 'seats')
    list_filter = ('seats',)
    search_fields = ('name',)


@admin.register(Table_Reservation)
class TableReservationAdmin(admin.ModelAdmin):
    list_display = ['user', 'table', 'reservation_start', 'reservation_end', 'number_of_party']
    search_fields = ['user__username', 'table__name', 'special_order']
    list_filter = ['reservation_start']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('type',)
    search_fields = ('type',)


@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display = ('item_name', 'item_price', 'category', 'image_preview')
    list_filter = ('category',)
    search_fields = ('item_name',)

    def image_preview(self, obj):
        if obj.images:
            return format_html('<img src="{}" width="60" />', obj.images.url)
        return "-"
    image_preview.short_description = 'Image'


class TableOrderItemInline(admin.TabularInline):
    model = TableOrderItem
    extra = 0


@admin.register(TableOrder)
class TableOrderAdmin(admin.ModelAdmin):
    list_display = ('reservation', 'ordered_items_summary')
    inlines = [TableOrderItemInline]
    search_fields = ('reservation__user__username',)

    def ordered_items_summary(self, obj):
        return ", ".join(f"{item.menu_item.item_name} (x{item.quantity})" for item in obj.items.all())

    ordered_items_summary.short_description = "Ordered Items"