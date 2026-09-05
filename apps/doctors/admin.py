from django.contrib import admin
from .models import Doctor, Specialty


@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "created_at")
    search_fields = ("name",)
    readonly_fields = ("created_at",)


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "full_name",
        "specialty",
        "visit_fee",
        "is_active",
        "created_at",
        "updated_at",
    )
    list_filter = ("is_active", "specialty", "created_at")
    search_fields = ("full_name", "specialty__name")
    list_editable = ("is_active", "visit_fee")
    list_select_related = ("specialty",)
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (
            "Doctor Information",
            {
                "fields": ("full_name", "specialty", "visit_fee", "is_active"),
            },
        ),
        (
            "Audit Metadata",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )


from django.contrib import admin
from .models import (
    AppointmentSlot,
    Appointment,
    Review,
    Wallet,
    WalletTransaction,
)


@admin.register(AppointmentSlot)
class AppointmentSlotAdmin(admin.ModelAdmin):
    list_display = ("id", "doctor", "starts_at", "is_active", "created_at")
    list_filter = ("is_active", "doctor")
    search_fields = ("doctor__full_name",)
    list_select_related = ("doctor",)
    readonly_fields = ("created_at",)


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
    search_fields = ("patient__username", "patient__email")
    list_select_related = ("patient", "slot", "completed_by")
    readonly_fields = ("booked_at",)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("id", "appointment", "rating", "created_at")
    list_filter = ("rating",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "balance", "updated_at")
    search_fields = ("user__username",)
    readonly_fields = ("updated_at",)


@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "wallet",
        "appointment",
        "type",
        "amount",
        "balance_after",
        "created_at",
    )
    list_filter = ("type", "created_at")
    list_select_related = ("wallet", "appointment")
    readonly_fields = ("created_at",)
