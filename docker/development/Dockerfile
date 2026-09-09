FROM python:3.12-slim

# تنظیم متغیرهای محیطی پایتون برای بهینه‌سازی کانتینر
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# نصب ابزارهای پایه برای کامپایل وابستگی‌های احتمالی دیتابیس
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# کپی و نصب وابستگی‌ها در یک لایه مجزا جهت استفاده بهینه از کش داکر
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# کپی سورس‌کد پروژه
COPY . /app/

EXPOSE 8000

# دستور پیش‌فرض اجرای سرور توسعه جنگو
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]