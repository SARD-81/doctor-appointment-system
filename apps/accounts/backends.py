# apps/accounts/backends.py
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

User = get_user_model()


class EmailAuthBackend(ModelBackend):
    """بک‌اند احراز هویت اختصاصی بر پایه ایمیل و رمز عبور."""

    def authenticate(self, request, email=None, password=None, **kwargs):
        # بررسی پشتیبانی از دریافت ایمیل به عنوان USERNAME_FIELD
        if email is None:
            email = kwargs.get(User.USERNAME_FIELD)

        # در صورت عدم ارسال ایمیل یا رمز عبور، احراز هویت رد می‌شود
        if email is None or password is None:
            return None

        # جستجوی کاربر بدون وابستگی به بزرگی و کوچکی حروف (Case-Insensitive)
        try:
            user = User.objects.get(email__iexact=email)
        except (User.DoesNotExist, User.MultipleObjectsReturned):
            return None

        # اعتبارسنجی رمز عبور و فعال بودن وضعیت کاربر (is_active=True)
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
