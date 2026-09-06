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
    cache.clear()
    yield
    cache.clear()


def _extract_otp_from_outbox(email_address: str) -> str:
    message = mail.outbox[-1]
    assert email_address in message.to
    return message.body.split("کد یک‌بار مصرف شما: ")[1].split("\n")[0].strip()


def test_generate_and_send_otp_success():
    email = "test@example.com"
    success, msg = generate_and_send_otp(email)

    assert success is True
    assert len(mail.outbox) == 1
    assert email in mail.outbox[0].to
    assert "کد یک‌بار مصرف شما:" in mail.outbox[0].body


def test_verify_otp_success_and_one_time_use():
    email = "user@example.com"
    generate_and_send_otp(email)
    otp = _extract_otp_from_outbox(email)

    # موفقیت در بار اول
    success, _ = verify_otp(email, otp)
    assert success is True

    # تست عدم استفاده مجدد (One-time use)
    reuse_success, _ = verify_otp(email, otp)
    assert reuse_success is False


def test_invalid_otp_deterministic_and_attempts():
    email = "user@example.com"
    generate_and_send_otp(email)
    actual_otp = _extract_otp_from_outbox(email)

    # تولید یک کد تضمین‌شده متفاوت با کد واقعی
    wrong_otp = f"{(int(actual_otp) + 1) % 1_000_000:06d}" if actual_otp != "999999" else "000001"

    success, msg = verify_otp(email, wrong_otp)
    assert success is False
    assert f"فرصت باقی‌مانده: {MAX_ATTEMPTS - 1}" in msg


def test_otp_invalidation_after_max_attempts():
    email = "attempts@example.com"
    generate_and_send_otp(email)
    actual_otp = _extract_otp_from_outbox(email)
    wrong_otp = f"{(int(actual_otp) + 1) % 1_000_000:06d}" if actual_otp != "999999" else "000001"

    for _ in range(MAX_ATTEMPTS - 1):
        success, _ = verify_otp(email, wrong_otp)
        assert success is False

    # تلاش پنجم: کد باید کاملاً باطل شود
    final_success, final_msg = verify_otp(email, wrong_otp)
    assert final_success is False
    assert "کد باطل شد" in final_msg

    # تست اینکه حتی کد صحیح هم دیگر کار نمی‌کند
    assert verify_otp(email, actual_otp)[0] is False


def test_resend_cooldown_rejection():
    email = "cooldown@example.com"
    generate_and_send_otp(email)

    # درخواست فوری دوم باید به دلیل کول‌داون رد شود
    success, msg = generate_and_send_otp(email)
    assert success is False
    assert "پیش از درخواست مجدد" in msg


def test_resend_invalidates_previous_otp():
    email = "resend@example.com"
    generate_and_send_otp(email)
    first_otp = _extract_otp_from_outbox(email)

    # شبیه‌سازی گذشتن کول‌داون با پاک کردن کلید آن
    cache.delete(f"cooldown_key_{_get_email_key(email)}")

    generate_and_send_otp(email)
    second_otp = _extract_otp_from_outbox(email)

    # کد اول باید باطل شده باشد
    assert verify_otp(email, first_otp)[0] is False
    # کد دوم باید معتبر باشد
    assert verify_otp(email, second_otp)[0] is True


def test_rate_limit_after_five_requests():
    email = "ratelimit@example.com"
    email_key = _get_email_key(email)

    # ۵ ارسال موفق با دور زدن کول‌داون
    for _ in range(MAX_REQUESTS_PER_WINDOW):
        cache.delete(f"cooldown_key_{email_key}")
        success, _ = generate_and_send_otp(email)
        assert success is True

    # درخواست ششم باید به علت ریت‌لیمیت ۱۵ دقیقه بلاک شود
    cache.delete(f"cooldown_key_{email_key}")
    success, msg = generate_and_send_otp(email)
    assert success is False
    assert "۱۵ دقیقه دیگر تلاش کنید" in msg


def test_email_send_failure_clears_cache_state():
    email = "fail@example.com"
    with patch(
        "apps.accounts.services.otp.send_mail",
        side_effect=Exception("SMTP down"),
    ):
        success, msg = generate_and_send_otp(email)

    assert success is False
    assert "خطا در ارسال ایمیل" in msg
    # کش نباید قفل مانده باشد و باید بتواند دوباره بدون کول‌داون درخواست دهد
    success_after, _ = generate_and_send_otp(email)
    assert success_after is True
