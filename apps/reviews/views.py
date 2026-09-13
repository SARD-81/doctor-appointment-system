from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import redirect
from django.views.decorators.http import require_POST

from apps.reviews.exceptions import (
    AppointmentNotCompletedError,
    ReviewAlreadyExistsError,
    ReviewOwnershipError,
)
from apps.reviews.forms import ReviewForm
from apps.reviews.services import ReviewService


@login_required
@require_POST
def create_review_view(request, appointment_id: int):
    """ثبت نظر فقط با POST؛ مالکیت و eligibility کاملاً در ReviewService بررسی می‌شوند."""
    form = ReviewForm(request.POST)
    if not form.is_valid():
        messages.error(request, "امتیاز باید عددی بین ۱ تا ۵ باشد.")
        return redirect("appointments:my_appointments")

    try:
        ReviewService.create_review(
            patient=request.user,
            appointment_id=appointment_id,
            rating=form.cleaned_data["rating"],
            comment=form.cleaned_data["comment"],
        )
    except ReviewOwnershipError as exc:
        # عدم افشای وجود نداشتن نوبت برای کاربر دیگر
        raise Http404("نوبت یافت نشد.") from exc
    except AppointmentNotCompletedError:
        messages.error(request, "ثبت نظر فقط برای نوبت‌های تکمیل‌شده امکان‌پذیر است.")
    except ReviewAlreadyExistsError:
        messages.error(request, "شما قبلاً برای این نوبت نظر ثبت کرده‌اید.")
    else:
        messages.success(request, "نظر و امتیاز شما با موفقیت ثبت شد.")

    return redirect("appointments:my_appointments")
