# Doctor Appointment System

A production-ready doctor appointment booking system built with Django, PostgreSQL, and Docker.

## Project Status

This project is currently under active development as part of a software engineering bootcamp team project.

## Core Features

- Doctor and specialty management
- Appointment scheduling and booking
- Wallet-based payments
- Email OTP authentication
- Doctor search
- Ratings and reviews
- Google OAuth
- Production-ready Docker setup

## Tech Stack

- Python 3.12
- Django 5.2
- PostgreSQL 16
- Docker & Docker Compose
- pytest
- Ruff

## Team

Three-person software engineering team.

Detailed setup and deployment documentation will be added as development progresses.
##  Quick Start & Running

Choose your target environment to start the application:

### Option 1: Development Environment (Recommended for Local Dev)

Runs Django with hot-reloading enabled via `compose.yml`.

1. **Clone the repository and enter the directory:**
   ```bash
   git clone <repository-url>
   cd doctor-appointment-system
   ```

2. **Setup environment variables:**
   ```bash
   cp .env.example .env
   # Ensure POSTGRES_* and SECRET_KEY are properly configured
   ```

3. **Build and start services:**
   ```bash
   docker compose up -d --build
   ```

4. **Apply database migrations:**
   ```bash
   docker compose exec web python manage.py migrate
   ```

5. **Create an admin account:**
   ```bash
   docker compose exec web python manage.py createsuperuser
   ```

6. **Open in browser:**
   - App: [http://localhost:8000](http://localhost:8000)
   - Admin Panel: [http://localhost:8000/admin](http://localhost:8000/admin)

---

### Option 2: Production Environment

Runs an optimized build using **Gunicorn** via `compose.production.yml`.

1. **Setup production environment variables:**
   ```bash
   cp .env.production.example .env.production
   # Ensure DEBUG=False and strong credentials are set
   ```

2. **Build and start production containers:**
   ```bash
   docker compose -f compose.production.yml up -d --build
   ```

3. **Run migrations and collect static assets:**
   ```bash
   docker compose -f compose.production.yml exec web python manage.py migrate
   docker compose -f compose.production.yml exec web python manage.py collectstatic --noinput
   ```

4. **Verify container health and logs:**
   ```bash
   docker compose -f compose.production.yml ps
   docker compose -f compose.production.yml logs -f web
   ```

