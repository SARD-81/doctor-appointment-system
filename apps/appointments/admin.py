from django.contrib import admin

from .models import Appointment, AppointmentSlot


@admin.register(AppointmentSlot)
class AppointmentSlotAdmin(admin.ModelAdmin):
    list_display = ("id", "doctor", "starts_at", "is_active", "created_at")
    list_filter = ("is_active", "doctor")
    search_fields = ("doctor__full_name", "doctor__specialty__name")
    list_select_related = ("doctor", "doctor__specialty")
    readonly_fields = ("created_at",)
    ordering = ("starts_at",)


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "patient",
        "slot",
        "status",
        "amount_paid",
        "booked_at",
        "completed_at",
        "completed_by",
    )
    list_filter = ("status", "booked_at")
    search_fields = (
        "=id",
        "patient__username",
        "patient__email",
        "slot__doctor__full_name",
    )
    autocomplete_fields = ("patient", "slot", "completed_by")
    list_select_related = ("patient", "slot__doctor", "completed_by")
    readonly_fields = ("booked_at",)
    ordering = ("-booked_at",)
