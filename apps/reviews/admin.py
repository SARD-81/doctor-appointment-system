from django.contrib import admin

from apps.reviews.models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("id", "appointment", "rating", "created_at")
    list_filter = ("rating", "created_at")
    search_fields = (
        "appointment__patient__email",
        "appointment__slot__doctor__full_name",
    )
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)
