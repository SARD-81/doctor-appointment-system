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


