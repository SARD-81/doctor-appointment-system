# apps/accounts/forms.py
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

User = get_user_model()


class UserRegisterForm(forms.ModelForm):
    """فرم ثبت‌نام اولیه کاربر و اعتبارسنجی اطلاعات هویتی."""

    password = forms.CharField(
        widget=forms.PasswordInput(),
        label="رمز عبور",
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(),
        label="تکرار رمز عبور",
    )

    class Meta:
        model = User
        fields = ("username", "email", "password")

    def clean(self):
        """بررسی تطابق کلمه‌های عبور و اعتبارسنجی شباهت پسورد با مشخصات کاربری."""
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        username = cleaned_data.get("username")
        email = cleaned_data.get("email")

        # بررسی تطابق رمز عبور با تکرار آن
        if password and confirm_password and password != confirm_password:
            self.add_error("confirm_password", "رمزهای عبور با هم مطابقت ندارند.")

        # اجرای ولیدیتورهای امنیتی جنگو با در نظر گرفتن نمونه کاربر موقت
        if password:
            candidate_user = User(username=username or "", email=email or "")
            try:
                validate_password(password, user=candidate_user)
            except ValidationError as error:
                self.add_error("password", error)

        return cleaned_data

    def clean_email(self):
        """اعتبارسنجی یکتایی ایمیل به صورت غیرحساس به حروف بزرگ و کوچک (Case-Insensitive)."""
        email = self.cleaned_data.get("email")
        if email:
            email = email.lower()
            if User.objects.filter(email__iexact=email).exists():
                raise forms.ValidationError("این ایمیل قبلاً ثبت‌ نام کرده است.")
        return email

    def clean_username(self):
        """اعتبارسنجی یکتایی نام کاربری در سیستم."""
        username = self.cleaned_data.get("username")
        if username:
            if User.objects.filter(username=username).exists():
                raise forms.ValidationError("این نام کاربری قبلاً انتخاب شده است.")
        return username

    def save(self, commit=True):
        """ذخیره کاربر با وضعیت غیرفعال (is_active=False) تا زمان تایید نهایی OTP."""
        user = super().save(commit=False)
        user.is_active = False
        user.set_password(self.cleaned_data.get("password"))

        if commit:
            user.save()
        return user


class VerifyOTPForm(forms.Form):
    """فرم اعتبارسنجی ساختار کد یک‌بار مصرف دریافتی از کاربر."""

    code = forms.CharField(
        max_length=6,
        min_length=6,
        label="کد تایید",
    )

    def clean_code(self):
        """بررسی عددی بودن کد و حفظ صفرهای اولیه (دقیقاً ۶ رقم)."""
        code = self.cleaned_data.get("code")
        if code:
            if not code.isdigit() or len(code) != 6:
                raise forms.ValidationError("کد تایید باید دقیقاً ۶ رقم عدد باشد.")
        return code


class UserLoginForm(forms.Form):
    """فرم ورود کاربران بر پایه ایمیل و رمز عبور."""

    email = forms.EmailField(label="ایمیل")
    password = forms.CharField(widget=forms.PasswordInput(), label="رمز عبور")
