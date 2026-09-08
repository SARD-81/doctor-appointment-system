# apps/accounts/tests/test_otp_service.py
from unittest.mock import patch

import pytest
from django.core import mail
from django.core.cache import cache

from apps.accounts.services.otp import (
    MAX_ATTEMPTS,
    MAX_REQUESTS_PER_WINDOW,
    _get_email_key,
    generate_and_send_otp,
    verify_otp,
)


@pytest.fixture(autouse=True)
def clear_cache():
    """پاک‌سازی کش پیش و پس از اجرای هر تست برای ایزولاسیون کامل."""
    cache.clear()
    yield
    cache.clear()


def _extract_otp_from_outbox(email_address: str) -> str:
    """استخراج کد OTP از متن آخرین ایمیل ارسالی در Outbox تست."""
    message = mail.outbox[-1]
    assert email_address in message.to
    return message.body.split("کد یک‌بار مصرف شما: ")[1].split("\n")[0].strip()


def test_generate_and_send_otp_success():
    """بررسی تولید و ارسال موفق کد یک‌بار مصرف به صندوق ایمیل کاربر."""
    email = "test@example.com"
    success, msg = generate_and_send_otp(email)

    assert success is True
    assert len(mail.outbox) == 1
    assert email in mail.outbox[0].to
    assert "کد یک‌بار مصرف شما:" in mail.outbox[0].body


def test_verify_otp_success_and_one_time_use():
    """اعتبارسنجی تایید موفق کد و باطل شدن آن پس از اولین استفاده (One-time use)."""
    email = "user@example.com"
    generate_and_send_otp(email)
    otp = _extract_otp_from_outbox(email)

    # تایید کد برای بار اول
    success, _ = verify_otp(email, otp)
    assert success is True

    # بررسی رد استفاده مجدد از همان کد
    reuse_success, _ = verify_otp(email, otp)
    assert reuse_success is False


def test_invalid_otp_deterministic_and_attempts():
    """شمارش و کاهش فرصت‌های باقی‌مانده در صورت ورود کد اشتباه."""
    email = "user@example.com"
    generate_and_send_otp(email)
    actual_otp = _extract_otp_from_outbox(email)

    # تضمین تولید کدی متفاوت با کد صادر شده
    wrong_otp = f"{(int(actual_otp) + 1) % 1_000_000:06d}" if actual_otp != "999999" else "000001"

    success, msg = verify_otp(email, wrong_otp)
    assert success is False
    assert f"فرصت باقی‌مانده: {MAX_ATTEMPTS - 1}" in msg


def test_otp_invalidation_after_max_attempts():
    """باطل‌سازی دائمی کد پس از اتمام حداکثر تعداد تلاش مجاز (۵ مرتبه)."""
    email = "attempts@example.com"
    generate_and_send_otp(email)
    actual_otp = _extract_otp_from_outbox(email)
    wrong_otp = f"{(int(actual_otp) + 1) % 1_000_000:06d}" if actual_otp != "999999" else "000001"

    # چهار بار ورود کد اشتباه
    for _ in range(MAX_ATTEMPTS - 1):
        success, _ = verify_otp(email, wrong_otp)
        assert success is False

    # تلاش پنجم و باطل شدن کامل کد
    final_success, final_msg = verify_otp(email, wrong_otp)
    assert final_success is False
    assert "کد باطل شد" in final_msg

    # اطمینان از عدم پذیرش حتی کد صحیح پس از باطل شدن
    assert verify_otp(email, actual_otp)[0] is False


def test_resend_cooldown_rejection():
    """جلوگیری از ارسال مجدد در بازه کول‌داون (۶۰ ثانیه)."""
    email = "cooldown@example.com"
    generate_and_send_otp(email)

    success, msg = generate_and_send_otp(email)
    assert success is False
    assert "پیش از درخواست مجدد" in msg


def test_resend_invalidates_previous_otp_deterministic():
    """تست قطعی باطل شدن کد قبلی پس از صدور مجدد با شبیه‌سازی مقادیر تصادفی."""
    email = "resend_mock@example.com"

    # تولید اولین کد با مقدار معین ۱۱۱۱۱۱
    with patch("apps.accounts.services.otp.secrets.randbelow", return_value=111111):
        generate_and_send_otp(email)

    # رفع بازه کول‌داون برای شبیه‌سازی مجاز شدن درخواست مجدد
    cache.delete(f"cooldown_key_{_get_email_key(email)}")

    # تولید دومین کد با مقدار معین ۲۲۲۲۲۲
    with patch("apps.accounts.services.otp.secrets.randbelow", return_value=222222):
        generate_and_send_otp(email)

    # کد اول باید نامعتبر و کد دوم معتبر باشد
    assert verify_otp(email, "111111")[0] is False
    assert verify_otp(email, "222222")[0] is True


def test_otp_expired_after_ttl():
    """بررسی رفتار سیستم در هنگام منقضی شدن کد بر اثر اتمام طول عمر ۵ دقیقه‌ای."""
    email = "ttl_test@example.com"
    generate_and_send_otp(email)
    otp = _extract_otp_from_outbox(email)

    # شبیه‌سازی انقضای کلید کش در ردیس
    cache.delete(f"otp_value_{_get_email_key(email)}")

    success, msg = verify_otp(email, otp)
    assert success is False
    assert "منقضی شده" in msg


def test_rate_limit_after_five_requests():
    """مسدودسازی موقت پس از ثبت ۵ درخواست در بازه ۱۵ دقیقه‌ای."""
    email = "ratelimit@example.com"
    email_key = _get_email_key(email)

    # ثبت ۵ درخواست متوالی با رفع کول‌داون
    for _ in range(MAX_REQUESTS_PER_WINDOW):
        cache.delete(f"cooldown_key_{email_key}")
        success, _ = generate_and_send_otp(email)
        assert success is True

    # درخواست ششم باید توسط ریت‌لیمیت رد شود
    cache.delete(f"cooldown_key_{email_key}")
    success, msg = generate_and_send_otp(email)
    assert success is False
    assert "۱۵ دقیقه دیگر تلاش کنید" in msg


def test_email_send_failure_clears_cache_state():
    """اطمینان از پاک‌سازی کش و لغو قفل در صورت بروز خطای لایه ارسال ایمیل."""
    email = "fail@example.com"
    with patch(
        "apps.accounts.services.otp.send_mail",
        side_effect=Exception("SMTP down"),
    ):
        success, msg = generate_and_send_otp(email)

    assert success is False
    assert "خطا در ارسال ایمیل" in msg

    # امکان ارسال مجدد بلافاصله پس از شکست
    success_after, _ = generate_and_send_otp(email)
    assert success_after is True
