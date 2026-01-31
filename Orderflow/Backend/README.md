# Backend (Django + DRF)

This directory contains the Django backend for OrderFlow, using Django REST Framework for API endpoints, PostgreSQL for data, Redis for caching and Celery, and JWT for authentication.

---

## Tech Stack
- Django 4.x
- Django REST Framework
- PostgreSQL
- Redis
- Celery
- JWT Authentication

---

## Installation & Setup

### 1. Create Virtual Environment
```sh
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 2. Install Requirements
```sh
pip install -r requirements.txt
```

### 3. Environment Variables
- Copy `.env.example` to `.env` and fill in required values.

### 4. Run Migrations
```sh
python manage.py migrate
```

### 5. Create Superuser
```sh
python manage.py createsuperuser
```

### 6. Run Development Server
```sh
python manage.py runserver
```

---

## Celery (Async Tasks)

### Start Celery Worker
```sh
celery -A config worker -l info
```

### Start Celery Beat (Scheduled Tasks)
```sh
celery -A config beat -l info
```

---

## Production Notes
- Set `DEBUG=False` in production.
- Use strong, unique `SECRET_KEY`.
- Set `ALLOWED_HOSTS` appropriately.
- Use secure database and Redis credentials.
- Use HTTPS in production.

---

## Useful Commands
- Collect static files:
  ```sh
  python manage.py collectstatic
  ```
- Run tests:
  ```sh
  pytest
  ```

---

## Deployment (Railway/EC2)
- Use Docker or a Python environment.
- Set environment variables securely (never commit secrets).
- Run migrations and create superuser.
- Start Celery worker and beat.

---

## Additional Notes
- Do not commit secrets to the repository.
- For local dev, use the provided `docker-compose.yml` for all services.
