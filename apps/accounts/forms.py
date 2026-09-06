from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()


class UserRegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())
    confirm_password = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = User
        fields = ("username", "email", "password")

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        # بررسی تطابق پسوردها
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("رمزهای عبور با هم مطابقت ندارند.")

        return cleaned_data

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email:
            email = email.lower()
            # بررسی یکتایی ایمیل
            if User.objects.filter(email=email).exists():
                raise forms.ValidationError("این ایمیل قبلاً ثبت‌ نام کرده است.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if username:
            # بررسی یکتایی نام کاربری
            if User.objects.filter(username=username).exists():
                raise forms.ValidationError("این نام کاربری قبلاً انتخاب شده است.")
        return username

    def save(self, commit=True):
        # ساخت کاربر بدون ذخیره نهایی در دیتابیس برای اعمال تغییرات
        user = super().save(commit=False)

        # تنظیم وضعیت کاربر به غیرفعال (تا زمان تایید OTP)
        user.is_active = False

        # هش کردن امن رمز عبور
        user.set_password(self.cleaned_data.get("password"))

        if commit:
            user.save()
        return user


class VerifyOTPForm(forms.Form):
    code = forms.CharField(max_length=6, min_length=6, label="کد تایید")

    def clean_code(self):
        code = self.cleaned_data.get("code")
        if code:
            # بررسی اینکه دقیقاً ۶ رقم و تماماً عددی باشد (حفظ صفرهای اولیه)
            if not code.isdigit() or len(code) != 6:
                raise forms.ValidationError("کد تایید باید دقیقاً ۶ رقم عدد باشد.")
        return code


class UserLoginForm(forms.Form):
    email = forms.EmailField(label="ایمیل")
    password = forms.CharField(widget=forms.PasswordInput(), label="رمز عبور")
