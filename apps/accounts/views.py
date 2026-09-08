from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from apps.accounts.forms import UserLoginForm, UserRegisterForm, VerifyOTPForm
from apps.accounts.services.otp import generate_and_send_otp, verify_otp

User = get_user_model()
PENDING_VERIFICATION_SESSION_KEY = "pending_verification_user_id"
EMAIL_AUTH_BACKEND = "apps.accounts.backends.EmailAuthBackend"


def _get_pending_user(request):
    user_id = request.session.get(PENDING_VERIFICATION_SESSION_KEY)
    if not user_id:
        return None

    try:
        user = User.objects.get(pk=user_id, is_active=False)
    except User.DoesNotExist:
        request.session.pop(PENDING_VERIFICATION_SESSION_KEY, None)
        return None

    return user


def _mask_email(email):
    local_part, separator, domain = email.partition("@")
    if not separator:
        return email
    if len(local_part) <= 2:
        masked_local = f"{local_part[:1]}*"
    else:
        masked_local = f"{local_part[0]}{'*' * (len(local_part) - 2)}{local_part[-1]}"
    return f"{masked_local}@{domain}"


def _is_safe_next_url(request, next_url):
    return bool(next_url) and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    )


def register_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            request.session[PENDING_VERIFICATION_SESSION_KEY] = user.pk

            success, service_message = generate_and_send_otp(user.email)
            if success:
                messages.success(request, service_message)
            else:
                messages.error(request, service_message)

            return redirect("accounts:verify_otp")
    else:
        form = UserRegisterForm()

    return render(request, "accounts/register.html", {"form": form})


def verify_otp_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    user = _get_pending_user(request)
    if user is None:
        messages.info(request, "برای تأیید حساب، ابتدا ثبت‌نام را کامل کنید.")
        return redirect("accounts:register")

    if request.method == "POST":
        form = VerifyOTPForm(request.POST)
        if form.is_valid():
            success, service_message = verify_otp(user.email, form.cleaned_data["code"])
            if success:
                user.is_active = True
                user.save(update_fields=["is_active"])
                auth_login(request, user, backend=EMAIL_AUTH_BACKEND)
                request.session.pop(PENDING_VERIFICATION_SESSION_KEY, None)
                messages.success(request, "حساب شما با موفقیت تأیید شد.")
                return redirect("home")

            messages.error(request, service_message)
    else:
        form = VerifyOTPForm()

    return render(
        request,
        "accounts/verify_otp.html",
        {
            "form": form,
            "email_hint": _mask_email(user.email),
        },
    )


@require_POST
def resend_otp_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    user = _get_pending_user(request)
    if user is None:
        messages.info(request, "برای دریافت کد جدید، ابتدا ثبت‌نام را کامل کنید.")
        return redirect("accounts:register")

    success, service_message = generate_and_send_otp(user.email)
    if success:
        messages.success(request, service_message)
    else:
        messages.warning(request, service_message)

    return redirect("accounts:verify_otp")


def login_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    next_url = request.POST.get("next") or request.GET.get("next", "")

    if request.method == "POST":
        form = UserLoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                request,
                email=form.cleaned_data["email"],
                password=form.cleaned_data["password"],
            )
            if user is None:
                form.add_error(None, "ایمیل یا رمز عبور صحیح نیست.")
            else:
                auth_login(request, user)
                request.session.pop(PENDING_VERIFICATION_SESSION_KEY, None)
                messages.success(request, "با موفقیت وارد حساب خود شدید.")
                if _is_safe_next_url(request, next_url):
                    return redirect(next_url)
                return redirect("home")
    else:
        form = UserLoginForm()

    return render(
        request,
        "accounts/login.html",
        {
            "form": form,
            "next_url": next_url,
        },
    )


@require_POST
def logout_view(request):
    auth_logout(request)
    messages.success(request, "از حساب کاربری خارج شدید.")
    return redirect("home")
