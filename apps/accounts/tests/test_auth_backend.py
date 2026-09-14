# apps/accounts/tests/test_auth_backend.py
import pytest
from django.contrib.auth import authenticate, get_user_model
from django.db import IntegrityError

from apps.accounts.backends import EmailAuthBackend
from apps.accounts.forms import UserRegisterForm, VerifyOTPForm

User = get_user_model()


@pytest.mark.django_db
def test_email_auth_backend_success():
    """بررسی موفقیت احراز هویت با ایمیل و رمز عبور صحیح."""
    email = "active_user@example.com"
    password = "SecurePassword123!"
    User.objects.create_user(
        username="active_user",
        email=email,
        password=password,
        is_active=True,
    )

    user = authenticate(email=email, password=password)
    assert user is not None
    assert user.email == email


@pytest.mark.django_db
def test_email_auth_backend_inactive_user():
    """عدم اجازه ورود به کاربری که وضعیت حساب او غیرفعال (is_active=False) است."""
    email = "inactive_user@example.com"
    password = "SecurePassword123!"
    User.objects.create_user(
        username="inactive_user",
        email=email,
        password=password,
        is_active=False,
    )

    user = authenticate(email=email, password=password)
    assert user is None


@pytest.mark.django_db
def test_email_auth_backend_wrong_password():
    """رد احراز هویت در صورت وارد کردن رمز عبور نادرست."""
    email = "user@example.com"
    User.objects.create_user(
        username="user",
        email=email,
        password="CorrectPassword123!",
        is_active=True,
    )

    user = authenticate(email=email, password="WrongPassword123!")
    assert user is None


@pytest.mark.django_db
def test_email_auth_backend_unknown_email():
    """رد احراز هویت در صورت عدم وجود ایمیل در پایگاه داده."""
    user = authenticate(email="nonexistent@example.com", password="SomePassword123!")
    assert user is None


@pytest.mark.django_db
def test_email_auth_backend_case_insensitive_login():
    """بررسی عدم وابستگی جستجوی ایمیل در زمان ورود به حروف بزرگ و کوچک (Case-Insensitive)."""
    email = "CaseSensitive@Example.Com"
    password = "SecurePassword123!"
    User.objects.create_user(
        username="case_user",
        email=email,
        password=password,
        is_active=True,
    )

    # تلاش برای ورود با حروف کوچک
    user = authenticate(email="casesensitive@example.com", password=password)
    assert user is not None
    assert user.username == "case_user"


@pytest.mark.django_db
def test_email_auth_backend_get_user_active():
    """متد get_user باید شیء کاربر فعال را برگرداند."""
    user = User.objects.create_user(
        username="active_session_user",
        email="active_session@example.com",
        password="SecurePassword123!",
        is_active=True,
    )
    backend = EmailAuthBackend()
    retrieved_user = backend.get_user(user.pk)
    assert retrieved_user == user


@pytest.mark.django_db
def test_email_auth_backend_get_user_inactive():
    """متد get_user برای کاربر غیرفعال باید مقدار None برگرداند (ابطال نشست)."""
    user = User.objects.create_user(
        username="inactive_session_user",
        email="inactive_session@example.com",
        password="SecurePassword123!",
        is_active=False,
    )
    backend = EmailAuthBackend()
    retrieved_user = backend.get_user(user.pk)
    assert retrieved_user is None


@pytest.mark.django_db
def test_user_register_form_creates_inactive_user():
    """اطمینان از ایجاد کاربر با وضعیت غیرفعال (is_active=False) پس از ثبت‌نام اولیه."""
    data = {
        "username": "new_patient",
        "email": "patient@example.com",
        "password": "StrongPassword123!",
        "confirm_password": "StrongPassword123!",
    }
    form = UserRegisterForm(data=data)
    assert form.is_valid()
    user = form.save()

    assert user.pk is not None
    assert user.is_active is False
    assert user.check_password("StrongPassword123!")


@pytest.mark.django_db
def test_user_register_form_duplicate_email():
    """رد ثبت‌نام در صورت تکراری بودن ایمیل حتی با تغییر حروف بزرگ و کوچک."""
    User.objects.create_user(
        username="existing_user",
        email="existing@example.com",
        password="Password123!",
    )

    form = UserRegisterForm(
        data={
            "username": "unique_username",
            "email": "EXISTING@example.com",
            "password": "Password123!",
            "confirm_password": "Password123!",
        }
    )
    assert not form.is_valid()
    assert "این ایمیل قبلاً ثبت‌ نام کرده است." in form.errors["email"]


@pytest.mark.django_db(transaction=True)
def test_database_rejects_case_insensitive_duplicate_email():
    User.objects.create_user(
        username="first_case_user",
        email="CaseDuplicate@Example.com",
        password="Password123!",
    )

    with pytest.raises(IntegrityError):
        User.objects.create_user(
            username="second_case_user",
            email="caseduplicate@example.com",
            password="Password123!",
        )


@pytest.mark.django_db
def test_user_register_form_duplicate_username():
    """رد ثبت‌نام در صورت تکراری بودن نام کاربری."""
    User.objects.create_user(
        username="existing_username",
        email="user1@example.com",
        password="Password123!",
    )

    form = UserRegisterForm(
        data={
            "username": "existing_username",
            "email": "user2@example.com",
            "password": "Password123!",
            "confirm_password": "Password123!",
        }
    )
    assert not form.is_valid()
    assert "این نام کاربری قبلاً انتخاب شده است." in form.errors["username"]


@pytest.mark.django_db
def test_user_register_form_password_mismatch():
    """اعتبارسنجی عدم تطابق کلمه عبور و تکرار آن در فرم ثبت‌نام."""
    form = UserRegisterForm(
        data={
            "username": "test_user",
            "email": "test@example.com",
            "password": "Password123!",
            "confirm_password": "DifferentPassword123!",
        }
    )
    assert not form.is_valid()
    assert "رمزهای عبور با هم مطابقت ندارند." in form.errors["confirm_password"]


@pytest.mark.django_db
def test_user_register_form_weak_password():
    """اعتبارسنجی اعمال قوانین امنیتی جنگو (validate_password) روی فرم ثبت‌نام."""
    form = UserRegisterForm(
        data={
            "username": "weak_pwd_user",
            "email": "weak@example.com",
            "password": "123",
            "confirm_password": "123",
        }
    )
    assert not form.is_valid()
    assert "password" in form.errors


def test_verify_otp_form_validation():
    """بررسی اعتبارسنجی طول و عددی بودن فیلد کد یک‌بار مصرف."""
    assert VerifyOTPForm(data={"code": "123456"}).is_valid()
    assert not VerifyOTPForm(data={"code": "12345"}).is_valid()
    assert not VerifyOTPForm(data={"code": "1234567"}).is_valid()
    assert not VerifyOTPForm(data={"code": "abcdef"}).is_valid()


def test_verify_otp_form_valid_with_leading_zero():
    """اطمینان از معتبر بودن کدهای ۶ رقمی دارای صفر اولیه (حفظ فرمت رشته‌ای)."""
    form = VerifyOTPForm(data={"code": "001234"})
    assert form.is_valid()
    assert form.cleaned_data["code"] == "001234"


@pytest.mark.django_db
def test_user_register_form_password_similar_to_attributes():
    """اعتبارسنجی رد رمز عبور به دلیل شباهت بیش از حد به نام کاربری یا ایمیل."""
    form = UserRegisterForm(
        data={
            "username": "superpatient",
            "email": "superpatient@example.com",
            "password": "superpatient_123",
            "confirm_password": "superpatient_123",
        }
    )
    assert not form.is_valid()
    assert "password" in form.errors
