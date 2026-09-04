import hashlib
import secrets

from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail

OTP_TTL = 300  # 5 minutes
COOLDOWN_TTL = 60  # 60 seconds
MAX_ATTEMPTS = 5
RATE_LIMIT_TTL = 900  # 15 minutes
MAX_REQUESTS_PER_WINDOW = 5


def _get_email_key(email: str) -> str:
    clean_email = email.strip().lower()
    return hashlib.sha256(clean_email.encode()).hexdigest()


def _hash_otp(code: str, secret_key: str) -> str:
    raw_data = f"{code}:{secret_key}"
    return hashlib.sha256(raw_data.encode()).hexdigest()


def generate_and_send_otp(email: str) -> tuple[bool, str]:
    email_key = _get_email_key(email)

    otp_key = f"otp_value_{email_key}"
    cooldown_key = f"cooldown_key_{email_key}"
    rate_limit_key = f"rate_limit_key_{email_key}"
    attempts_key = f"attempts_key_{email_key}"

    if cache.get(cooldown_key):
        return False, "لطفاً پیش از درخواست مجدد، چند لحظه صبر کنید."

    request_count = cache.get(rate_limit_key, 0)
    if request_count >= MAX_REQUESTS_PER_WINDOW:
        return (
            False,
            "تعداد درخواست‌های شما بیش از حد مجاز است. لطفاً ۱۵ دقیقه دیگر تلاش کنید.",
        )

    # تولید کد ۶ رقمی با پشتیبانی کامل از صفرهای ابتدایی
    otp = f"{secrets.randbelow(1_000_000):06d}"
    hashed_otp = _hash_otp(otp, settings.SECRET_KEY)

    # ذخیره در کش
    cache.set(otp_key, hashed_otp, timeout=OTP_TTL)
    cache.set(cooldown_key, True, timeout=COOLDOWN_TTL)
    cache.set(attempts_key, 0, timeout=OTP_TTL)

    # مدیریت پنجره زمانی Rate Limit
    if request_count == 0:
        cache.set(rate_limit_key, 1, timeout=RATE_LIMIT_TTL)
    else:
        cache.incr(rate_limit_key)

    # ارسال رسمی از طریق Django Email Backend
    subject = "کد تأیید ثبت‌نام"
    message = f"کد یک‌بار مصرف شما: {otp}\nاین کد تا ۵ دقیقه معتبر است."
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email.strip().lower()],
        fail_silently=False,
    )

    return True, "کد تأیید با موفقیت ارسال شد."


def verify_otp(email: str, input_code: str) -> tuple[bool, str]:
    email_key = _get_email_key(email)
    otp_key = f"otp_value_{email_key}"
    attempts_key = f"attempts_key_{email_key}"
    cooldown_key = f"cooldown_key_{email_key}"

    stored_hash = cache.get(otp_key)
    if not stored_hash:
        return False, "کد تأیید منقضی شده یا درخواست نشده است."

    attempts_count = cache.get(attempts_key, 0)
    if attempts_count >= MAX_ATTEMPTS:
        cache.delete(otp_key)
        cache.delete(attempts_key)
        return (
            False,
            "تعداد دفعات تلاش ناموفق بیش از حد مجاز است. لطفاً دوباره درخواست کد دهید.",
        )

    input_hash = _hash_otp(input_code.strip(), settings.SECRET_KEY)

    if secrets.compare_digest(stored_hash, input_hash):
        cache.delete(otp_key)
        cache.delete(attempts_key)
        cache.delete(cooldown_key)
        return True, "احراز هویت با موفقیت انجام شد."

    # افزایش تلاش‌های ناموفق
    if attempts_count == 0:
        cache.set(attempts_key, 1, timeout=OTP_TTL)
        new_attempts = 1
    else:
        new_attempts = cache.incr(attempts_key)

    # اگر به سقف تلاش رسید، فوراً باطل شود
    if new_attempts >= MAX_ATTEMPTS:
        cache.delete(otp_key)
        cache.delete(attempts_key)
        return (
            False,
            "تعداد دفعات تلاش ناموفق بیش از حد مجاز است. کد باطل شد، لطفاً مجدداً درخواست دهید.",
        )

    remaining_attempts = MAX_ATTEMPTS - new_attempts
    return (
        False,
        f"کد وارد شده نامعتبر است. فرصت باقی‌مانده: {remaining_attempts} بار",
    )
