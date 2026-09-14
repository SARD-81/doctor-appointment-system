FROM python:3.12-slim

# تنظیم متغیرهای محیطی پایتون برای بهینه‌سازی اجرا
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# کپی و نصب مستقیم وابستگی‌ها بر اساس نسخه مشخص مخزن
COPY requirements.txt /app/
#RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir --default-timeout=1000 -i https://mirror-pypi.runflare.com/simple/ --trusted-host mirror-pypi.runflare.com -r requirements.txt

COPY . /app/

EXPOSE 8000

# دستور پیش‌فرض اجرای سرور توسعه
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
