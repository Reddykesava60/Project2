# 🍽️ DineFlow2

Email	Password	Role	Restaurant
admin@dineflow.com	admin123	Platform Admin	—
owner@restaurant.com	owner123	Restaurant Owner	The Italian Place
staff@restaurant.com	staff123	Staff (can_collect_cash=True)	The Italian Place
cook@restaurant.com	cook123	Staff (can_collect_cash=False)	The Italian Place
http://localhost:3000/r/italian-place

cd Backend;python manage.py runserver 8000
cd frontend;npm run dev

<div align="center">

![DineFlow2](https://img.shields.io/badge/DineFlow2-Restaurant%20SaaS-2563EB?style=for-the-badge)
![Django](https://img.shields.io/badge/Django-5.x-092E20?style=for-the-badge&logo=django&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-16-000000?style=for-the-badge&logo=next.js&logoColor=white)
![React](https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?style=for-the-badge&logo=typescript&logoColor=white)

**Multi-Tenant Restaurant Management Platform**

*QR-based ordering • Real-time kitchen operations • Razorpay payments • Owner analytics*

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Quick Start](#-quick-start)
- [Environment Configuration](#-environment-configuration)
- [API Documentation](#-api-documentation)
- [User Roles](#-user-roles)
- [Payment Integration](#-payment-integration)
- [Testing](#-testing)
- [Deployment](#-deployment)

---

## 🎯 Overview

**DineFlow2** is a production-ready, multi-tenant restaurant SaaS platform. Customers scan QR codes to browse menus and place orders. Staff manage real-time kitchen operations. Owners access analytics and business insights.

### Key Capabilities

| Feature | Description |
|---------|-------------|
| **QR Ordering** | Customers scan table QR codes, browse menu, and order instantly |
| **Real-time Kitchen** | Staff dashboard with live order updates (SWR polling) |
| **Payment Processing** | Razorpay UPI/card integration with cryptographic verification |
| **Multi-tenancy** | Complete data isolation per restaurant |
| **Role-based Access** | Platform admin, restaurant owner, staff roles |
| **Audit Logging** | Full traceability for all order state changes |

---

## ✨ Features

### Customer Experience
- 📱 Mobile-optimized QR ordering interface
- 🍕 Browse categories, view items with images & prices
- 🛒 Cart management with quantity controls
- 💳 UPI / Cash payment options
- 📊 Order status tracking

### Staff Operations
- 📋 Active orders dashboard (pending → preparing → ready → completed)
- ⚡ One-click status updates
- 💵 Cash order creation at counter
- 🔔 Real-time order notifications

### Owner Dashboard
- 📈 Revenue analytics and order statistics
- 🍽️ Menu management (categories, items, pricing)
- 👥 Staff user management
- 📊 Order history and reporting
- 🔗 QR code generation for tables

### Platform Admin
- 🏢 Multi-restaurant management
- 👤 User administration
- ⚙️ System configuration

---

## 🛠️ Tech Stack

### Backend
| Technology | Version | Purpose |
|------------|---------|---------|
| Django | 5.x | Web framework |
| Django REST Framework | 3.15+ | API layer |
| SimpleJWT | 5.3+ | JWT authentication |
| DRF Spectacular | 0.27+ | OpenAPI/Swagger docs |
| Razorpay SDK | 1.4+ | Payment gateway |
| PostgreSQL / SQLite | 15 / 3 | Database |

### Frontend
| Technology | Version | Purpose |
|------------|---------|---------|
| Next.js | 16 | React framework (App Router) |
| React | 19 | UI library |
| TypeScript | 5 | Type safety |
| Tailwind CSS | 4.x | Styling |
| Radix UI | Latest | Accessible components |
| SWR | 2.3+ | Data fetching & caching |
| Zustand | 5.x | State management |
| Zod | 3.x | Schema validation |

---

## 📁 Project Structure

```
DineFlow2/
├── Backend/                    # Django API server
│   ├── apps/
│   │   ├── core/              # Audit logs, permissions, utilities
│   │   ├── menu/              # Categories & menu items
│   │   ├── orders/            # Order management & payments
│   │   ├── restaurants/       # Restaurant & QR management
│   │   └── users/             # User authentication & roles
│   ├── config/                # Django settings & URLs
│   ├── templates/             # Email templates
│   ├── manage.py
│   ├── requirements.txt
│   └── .env                   # Environment variables
│
├── frontend/                   # Next.js application
│   ├── app/                   # App Router pages
│   │   ├── admin/            # Platform admin pages
│   │   ├── login/            # Authentication
│   │   ├── owner/            # Owner dashboard
│   │   ├── r/[slug]/         # Customer QR ordering
│   │   └── staff/            # Staff operations
│   ├── components/            # React components
│   │   ├── ui/               # Base UI components
│   │   ├── customer/         # Customer-facing components
│   │   ├── staff/            # Staff components
│   │   └── shared/           # Shared components
│   ├── lib/                   # Utilities & API client
│   ├── hooks/                 # Custom React hooks
│   ├── contexts/              # React contexts
│   └── types/                 # TypeScript definitions
│
├── docker-compose.yml          # Docker orchestration
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+ (pnpm recommended)
- PostgreSQL 15 (optional, SQLite works for dev)

### Option 1: Docker Compose (Recommended)

```bash
# Clone and start all services
git clone <repository-url>
cd DineFlow2
docker compose up --build
```

Services will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/api/
- API Docs: http://localhost:8000/api/docs/

### Option 2: Manual Setup

#### Backend Setup

```powershell
# Navigate to backend
cd Backend

# Create virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1  # Windows
# source .venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment (copy and edit .env)
# See Environment Configuration section below

# Run migrations
python manage.py migrate

# (Optional) Load sample data
python seed_data.py

# Start server
python manage.py runserver 8000
```

#### Frontend Setup

```powershell
# Navigate to frontend
cd frontend


# Install dependencies
pnpm install  # or npm install

# Create .env.local
# NEXT_PUBLIC_API_URL=http://localhost:8000/api

# Start development server
pnpm dev  # or npm run dev
```

---

## ⚙️ Environment Configuration

### Backend (.env)

```env
# Django
DEBUG=True
SECRET_KEY=your-secret-key-generate-with-django
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (SQLite for dev)
USE_SQLITE=True

# Database (PostgreSQL for production)
# USE_SQLITE=False
# DB_NAME=dineflow2
# DB_USER=postgres
# DB_PASSWORD=password
# DB_HOST=localhost
# DB_PORT=5432

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000

# JWT (minutes)
ACCESS_TOKEN_LIFETIME=60
REFRESH_TOKEN_LIFETIME=1440

# QR Code Security
QR_HMAC_SECRET=your-32-char-secret-here

# Razorpay Payment Gateway
RAZORPAY_KEY_ID=rzp_test_xxxxx
RAZORPAY_KEY_SECRET=your_secret
RAZORPAY_WEBHOOK_SECRET=your_webhook_secret
RAZORPAY_LIVE_MODE=True           # True for production
RAZORPAY_FORCE_SUCCESS=False      # NEVER True in production

# Frontend URL
FRONTEND_URL=http://localhost:3000

# Regional
DEFAULT_CURRENCY=INR
DEFAULT_TIMEZONE=Asia/Kolkata
```

### Frontend (.env.local)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

---

## 📚 API Documentation

### Interactive Docs

| URL | Description |
|-----|-------------|
| `/api/docs/` | Swagger UI |
| `/api/redoc/` | ReDoc |
| `/api/schema/` | OpenAPI JSON |

### Key Endpoints

#### Authentication
```
POST /api/auth/login/          # Login, returns JWT tokens
POST /api/auth/refresh/        # Refresh access token
GET  /api/auth/me/             # Current user profile
```

#### Orders (Staff/Owner)
```
GET  /api/orders/              # List orders (owner: all, staff: active)
GET  /api/orders/active/       # Active orders only
POST /api/orders/staff/create/ # Staff creates cash order
POST /api/orders/{id}/update_status/  # Update order status
POST /api/orders/{id}/collect-cash/   # Mark cash collected
```

#### Public (Customer QR Flow)
```
GET  /api/public/r/{slug}/menu/           # Get restaurant menu
POST /api/public/r/{slug}/orders/         # Create order (cash)
POST /api/public/r/{slug}/payment/initiate/  # Initiate UPI payment
POST /api/public/r/{slug}/payment/verify/    # Verify & create UPI order
```

#### Restaurant Management (Owner)
```
GET  /api/restaurants/         # List owner's restaurants
POST /api/restaurants/         # Create restaurant
GET  /api/menu/categories/     # Menu categories
POST /api/menu/items/          # Create menu item
```

---

## 👥 User Roles

| Role | Access | Capabilities |
|------|--------|--------------|
| **Platform Admin** | `/admin/` | Full system access, all restaurants |
| **Restaurant Owner** | `/owner/` | Own restaurant(s), menu, staff, analytics |
| **Staff** | `/staff/` | Active orders only, status updates |
| **Customer** | `/r/{slug}/` | QR ordering (no login required) |

---

## 💳 Payment Integration

### Razorpay Flow

1. **Cash Orders**: Created immediately with `payment_method='cash'`, `payment_status='pending'`
2. **UPI Orders**: Two-step flow for security:
   - `POST /payment/initiate/` → Returns Razorpay order_id
   - Customer completes payment on Razorpay
   - `POST /payment/verify/` → SDK verifies signature, creates order only if valid

### Security Features

- **Cryptographic Verification**: Uses `razorpay.utility.verify_payment_signature()`
- **Webhook Support**: `verify_webhook_signature()` for async notifications
- **No Trust Frontend**: Payment verification happens server-side only
- **Simulation Mode**: `RAZORPAY_FORCE_SUCCESS=True` + `RAZORPAY_LIVE_MODE=False` for testing

### Order Status Flow

```
Customer Order:   pending → preparing → ready → completed
Cash Collection:  payment_status: pending → success
UPI Payment:      (verified) → payment_status: success, status: preparing
```

---

## 🧪 Testing

### Backend Tests

```powershell
cd Backend

# Run all tests
pytest

# Run with coverage
pytest --cov=apps

# Run specific test file
pytest test_e2e_order_flow.py -v
```

### Key Test Files

| File | Purpose |
|------|---------|
| `test_e2e_order_flow.py` | End-to-end order workflow |
| `test_e2e_validation.py` | Full validation suite |
| `test_staff_api.py` | Staff API endpoints |
| `test_customer_flow.py` | Customer ordering flow |

### Verification Scripts

```powershell
# Validate database schema
python validate_db.py

# Trace API calls with SQL
python trace_api.py

# Verify order visibility rules
python verify_orders_visibility.py
```

---

## 🚀 Deployment

### Production Checklist

- [ ] Set `DEBUG=False`
- [ ] Generate strong `SECRET_KEY`
- [ ] Configure PostgreSQL database
- [ ] Set `RAZORPAY_LIVE_MODE=True`
- [ ] Set `RAZORPAY_FORCE_SUCCESS=False`
- [ ] Configure HTTPS
- [ ] Set proper `ALLOWED_HOSTS`
- [ ] Set proper `CORS_ALLOWED_ORIGINS`
- [ ] Configure email settings
- [ ] Set up monitoring (Sentry optional)

### Docker Production

```bash
# Build production images
docker compose -f docker-compose.prod.yml up --build -d

# Run migrations
docker compose exec backend python manage.py migrate

# Collect static files
docker compose exec backend python manage.py collectstatic --no-input
```

### Gunicorn (Manual)

```bash
cd Backend
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

---

## 📄 License

Internal project. Do not redistribute without permission.

---

## 🤝 Contributing

1. Follow existing code style
2. Add tests for new features
3. Keep PRs focused and narrow
4. Update documentation as needed

---

<div align="center">

**Built with ❤️ for modern restaurants**

</div>
