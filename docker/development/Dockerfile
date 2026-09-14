FROM python:3.12-slim

# تنظیم متغیرهای محیطی پایتون برای بهینه‌سازی اجرا
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# کپی و نصب مستقیم وابستگی‌ها بر اساس نسخه مشخص مخزن
COPY requirements.txt requirements-dev.txt /app/
RUN pip install --no-cache-dir -r requirements-dev.txt


COPY . /app/

EXPOSE 8000

# دستور پیش‌فرض اجرای سرور توسعه
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
