from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.appointments.models import Appointment, AppointmentSlot


@admin.register(AppointmentSlot)
class AppointmentSlotAdmin(admin.ModelAdmin):
    """پیکربندی پنل ادمین برای مدیریت اسلات‌های زمانی پزشکان."""

    list_display = (
        "doctor",
        "starts_at",
        "is_active",
        "is_available_display",
        "created_at",
    )
    list_filter = ("is_active", "starts_at", "doctor")
    search_fields = ("doctor__full_name",)
    ordering = ("starts_at",)

    @admin.display(boolean=True, description=_("Available"))
    def is_available_display(self, obj: AppointmentSlot) -> bool:
        """نمایش وضعیت در دسترس بودن اسلات به صورت آیکون بولی در لیست."""
        return obj.is_available


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    """پیکربندی پنل ادمین برای مدیریت و رهگیری نوبت‌های ثبت‌شده."""

    list_display = (
        "id",
        "patient",
        "doctor_display",
        "slot_time_display",
        "status",
        "amount_paid",
        "booked_at",
    )
    list_filter = ("status", "booked_at")
    search_fields = (
        "patient__username",
        "patient__email",
        "slot__doctor__full_name",
    )
    readonly_fields = ("booked_at",)
    ordering = ("-booked_at",)

    @admin.display(description=_("Doctor"))
    def doctor_display(self, obj: Appointment) -> str:
        """نمایش نام پزشک مرتبط با نوبت."""
        return obj.slot.doctor.full_name

    @admin.display(description=_("Slot Time"))
    def slot_time_display(self, obj: Appointment) -> str:
        """نمایش تاریخ و زمان اسلات نوبت."""
        return obj.slot.starts_at.strftime("%Y-%m-%d %H:%M")
