import re
import pytest
from django.core import mail
from django.core.cache import cache

from apps.accounts.services.otp import (
    MAX_ATTEMPTS,
    generate_and_send_otp,
    verify_otp,
)


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()
    yield
    cache.clear()


def test_generate_and_send_otp_sends_email():
    email = "doctor@example.com"

    success, message = generate_and_send_otp(email)
    assert success is True
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [email]


def test_send_otp_sends_email():
    email = "doctor@example.com"
    generate_and_send_otp(email)

    # استفاده از ریجکس برای استخراج دقیق عدد ۶ رقمی از متن ایمیل
    match = re.search(r"\d{6}", mail.outbox[0].body)
    actual_otp = match.group(0)

    success, message = verify_otp(email, actual_otp)
    assert success is True


def test_verify_otp_invalid_code():
    email = "doctor@example.com"
    generate_and_send_otp(email)

    success, message = verify_otp(email, "000000")
    assert success is False


def test_verify_otp_max_attempts_lockout():
    email = "doctor@example.com"
    generate_and_send_otp(email)

    match = re.search(r"\d{6}", mail.outbox[0].body)
    correct_otp = match.group(0)

    for _ in range(MAX_ATTEMPTS):
        success, message = verify_otp(email, "000000")
        assert success is False

    success, message = verify_otp(email, correct_otp)
    assert success is False


def test_generate_otp_rate_limiting():
    email = "doctor@example.com"

    # درخواست اول باید موفق باشد
    success1, _ = generate_and_send_otp(email)
    assert success1 is True

    # درخواست دوم بلافاصله‌ی پشت سر هم باید به دلیل ریت‌لیمیت رد شود
    success2, message = generate_and_send_otp(email)
    assert success2 is False


def test_verify_otp_expired():
    email = "doctor@example.com"
    generate_and_send_otp(email)

    match = re.search(r"\d{6}", mail.outbox[0].body)
    correct_otp = match.group(0)

    # شبیه‌سازی انقضای کد با پاک کردن کش (انگار زمان اعتبار تمام شده است)
    cache.clear()

    # تلاش برای تایید کد بعد از انقضا باید شکست بخورد
    success, message = verify_otp(email, correct_otp)
    assert success is False