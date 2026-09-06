from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend, user_can_authenticate

User = get_user_model()


class EmailAuthBackend(ModelBackend):
    def authenticate(self, request, email=None, password=None, **kwargs):
        # اگر ایمیل به جای فیلد email توی kwargs فرستاده شده بود هم هندلش کنیم
        if email is None:
            email = kwargs.get(User.USERNAME_FIELD)

        if email is None:
            return None

        try:
            user = User.objects.get(email=email.lower())
        except (User.DoesNotExist, User.MultipleObjectsReturned):
            return None
        else:
            if user.check_password(password) and user_can_authenticate(user):
                return user
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
