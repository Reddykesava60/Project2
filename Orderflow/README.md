# OrderFlow
Email	Password	Role	Restaurant
admin@dineflow.com	admin123	Platform Admin	—
owner@restaurant.com	owner123	Restaurant Owner	The Italian Place
staff@restaurant.com	staff123	Staff (can_collect_cash=True)	The Italian Place
cook@restaurant.com	cook123	Staff (can_collect_cash=False)	The Italian Place
http://localhost:3000/r/italian-place

http://localhost:3000

http://localhost:8000

▶ How to run
From project root:
- docker compose up --build -d

cd Backend;python manage.py runserver 8000
cd frontend;npm run dev

To stop everything cleanly:
- docker compose down

If you only want to stop one service (e.g., frontend):
- docker compose stop frontend

If Docker is running in detached mode and you forgot:
- docker ps

| Action              | Command                         |
| ------------------- | ------------------------------- |
| Start everything    | `docker compose up`             |
| Start in background | `docker compose up -d`          |
| Stop everything     | `docker compose down`           |
| View logs           | `docker compose logs <service>` |


- echo "# OrderFlow" >> README.md
- git init
- git add README.md
- git commit -m "first commit"
- git branch -M main
- git remote add origin https://github.com/Reddykesava60/OrderFlow.git
- git push -u origin main
- OrderFlow is a multi-tenant restaurant operating system designed for modern, scalable, and secure food service management. It streamlines the entire order lifecycle from customer to staff, owner, and admin, supporting both in-house and online operations.

---

## Architecture Diagram (Text)

```
[Customer Web App] --API--> [Backend (Django/DRF)] <---> [PostgreSQL]
                                         |                |
                                         |                |
                                         v                v
                                   [Redis] <--- Celery Worker
                                         |
                                         v
                                 [Payment Gateway]

[Admin/Owner/Staff Web App] --API--> [Backend]
```

---

## Tech Stack
- **Frontend:** Next.js (React, App Router)
- **Backend:** Django + Django REST Framework
- **Database:** PostgreSQL
- **Cache/Queue:** Redis
- **Async Tasks:** Celery
- **Payments:** Razorpay, Stripe
- **Containerization:** Docker, Docker Compose

---

## How the System Works

- **Customer:** Browses menu, places orders, tracks status, pays online.
- **Staff:** Views incoming orders, updates status, manages tables.
- **Owner:** Manages restaurant settings, menu, staff, analytics.
- **Admin:** Oversees all tenants, manages compliance, audits, and platform-wide settings.

---

## High-Level Security Model
- Multi-tenancy: Data isolation per restaurant.
- JWT authentication for all API endpoints.
- Role-based access control (Customer, Staff, Owner, Admin).
- Secure password storage and session management.
- HTTPS enforced in production.
- No secrets or sensitive data in codebase.

---

## Local Development

### Prerequisites
- Docker & Docker Compose
- Node.js (v18+)
- Python 3.11+

### Quickstart

```sh
# 1. Clone the repository
$ git clone https://github.com/your-org/orderflow.git
$ cd orderflow

# 2. Copy environment variable templates and fill in required values
$ cp Backend/.env.example Backend/.env
$ cp frontend/.env.local.example frontend/.env.local

# 3. Start all services
$ docker-compose up --build

# 4. Access the app
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
```

---

## Deployment

### Frontend (Vercel)
- Connect the `frontend` directory to Vercel.
- Set environment variables in Vercel dashboard.
- Use `npm run build` for production builds.

### Backend (Railway/EC2)
- Deploy `Backend` with Docker or directly on Python environment.
- Set environment variables securely (Railway/EC2 secrets manager).
- Run migrations and create superuser.
- Start Celery worker and beat.

---

## Useful Commands

- **Backend migrations:**
  ```sh
  cd Backend
  python -m venv venv && venv\Scripts\activate  # Windows
  pip install -r requirements.txt
  python manage.py migrate
  python manage.py createsuperuser
  celery -A config worker -l info
  ```
- **Frontend dev:**
  ```sh
  cd frontend
  npm install
  npm run dev
  ```

---

## Support & Contribution
- Please see CONTRIBUTING.md (if available) or open an issue for help.

---

## License
- MIT (or your license here)
