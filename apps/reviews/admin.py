from django.contrib import admin

from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "appointment",
        "patient",
        "doctor",
        "rating",
        "created_at",
    )
    list_filter = (
        "rating",
        "created_at",
        "appointment__slot__doctor__specialty",
    )
    search_fields = (
        "=id",
        "appointment__patient__username",
        "appointment__patient__email",
        "appointment__slot__doctor__full_name",
        "comment",
    )
    autocomplete_fields = ("appointment",)
    list_select_related = (
        "appointment__patient",
        "appointment__slot__doctor__specialty",
    )
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    list_per_page = 25

    @admin.display(description="Patient", ordering="appointment__patient")
    def patient(self, obj):
        return obj.appointment.patient

    @admin.display(
        description="Doctor",
        ordering="appointment__slot__doctor__full_name",
    )
    def doctor(self, obj):
        return obj.appointment.slot.doctor
