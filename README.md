# ParkEase - Smart Urban Parking & Bay Reservation Platform

[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.0%2B-darkgreen.svg)](https://www.djangoproject.com/)
[![Razorpay](https://img.shields.io/badge/Payments-Razorpay%20Official-blueviolet.svg)](https://razorpay.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Bootstrap](https://img.shields.io/badge/UI-Bootstrap%205-purple.svg)](https://getbootstrap.com/)

**ParkEase** is a full-stack, enterprise-grade smart parking reservation platform designed to streamline urban mobility. Inspired by modern European parking ecosystems like JustPark, ParkEase connects **Motorists (Drivers)**, **Space Owners**, and **Platform Administrators** into a seamless, high-trust experience featuring interactive map discovery, guaranteed bay allocation, dual QR entry/exit passes, overstay clearance, and official Razorpay payments.

---

## 📸 Visual Previews

### 1. Motorist Home & Smart Facility Discovery
![Motorist Home Search](docs/screenshots/01_home_search.png)

### 2. Digital Entry/Exit Pass with Live Scannable QR Code
![Digital Ticket QR Pass](docs/screenshots/02_digital_ticket_qr.png)

### 3. Space Facility Details & Turn-by-Turn Directions
![Facility Details](docs/screenshots/03_lot_detail.png)

### 4. Space Checkout & Official Razorpay Gateway
![Checkout & Razorpay](docs/screenshots/04_book_lot_checkout.png)

---

## Project Credentials (All 3 Portals)

The application provides out-of-the-box role accounts for testing and evaluation across all three platform workflows:

| Role | Username / Email | Password | Access Portal URL |
| :--- | :--- | :--- | :--- |
| **Motorist / Driver** | `user@gmail.com` | `user123` | [`http://127.0.0.1:8000/accounts/login/`](http://127.0.0.1:8000/accounts/login/) |
| **Space Owner** | `owner@gmail.com` | `owner123` | [`http://127.0.0.1:8000/accounts/login/`](http://127.0.0.1:8000/accounts/login/) |
| **Super Administrator** | `admin` | `admin123` | [`http://127.0.0.1:8000/admin-panel/login/`](http://127.0.0.1:8000/admin-panel/login/) |

---

## Installation & Setup Guide

### Windows

```bash
# 1. Clone the repository
git clone https://github.com/brainybeamGit/ParkEase-Django-P1.git
cd ParkEase-Django-P1

# 2. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run database migrations
python manage.py migrate

# 5. Create a superuser (admin account)
python manage.py createsuperuser

# 6. Seed initial data (optional)
python scripts/seeds.py

# 7. Start the development server
python manage.py runserver
```

Open `http://127.0.0.1:8000` in your browser.

---

### macOS / Linux

```bash
# 1. Clone the repository
git clone https://github.com/brainybeamGit/ParkEase-Django-P1.git
cd ParkEase-Django-P1

# 2. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run database migrations
python3 manage.py migrate

# 5. Create a superuser (admin account)
python3 manage.py createsuperuser

# 6. Seed initial data (optional)
python3 scripts/seeds.py

# 7. Start the development server
python3 manage.py runserver
```

Open `http://127.0.0.1:8000` in your browser.

---

##  Project Architecture & Skeleton

```text
ParkEase/
├── accounts/                     # User management & motorist garage
│   ├── migrations/               # Database schema versions
│   ├── models.py                 # Custom Profile, Vehicle, EmailDeliveryLog models
│   ├── views.py                  # Driver login, register, profile, garage views
│   └── urls.py                   # Motorist authentication routing
│
├── admin_panel/                  # Super Administrator Management Studio
│   ├── models.py                 # PlatformPricingRule, Coupon, PlatformComplaint models
│   ├── views.py                  # Revenue analytics, payout approvals, pricing controls
│   └── urls.py                   # Admin endpoints (/admin-panel/*)
│
├── lot_owner_panel/              # Space Owner Management Suite
│   ├── models.py                 # ParkingLot, ParkingSlot, OwnerNotification models
│   ├── views.py                  # Facility listing, bay occupancy matrix, earnings
│   └── urls.py                   # Space owner routing (/lot-owner/*)
│
├── parking/                      # Core search, booking & ticketing engine
│   ├── models.py                 # Booking, OverstayRecord, LotReview models
│   ├── views.py                  # Search, bay reservation, ticket, QR scanner, overstay
│   └── urls.py                   # Booking lifecycle endpoints
│
├── parkease/                     # Project configuration & background services
│   ├── email_service.py          # Asynchronous SMTP notification dispatcher
│   ├── settings.py               # Django configuration & gateway settings
│   ├── urls.py                   # Master URL routing table
│   └── wsgi.py                   # Production WSGI application
│
├── scripts/                      # Management & database automation
│   └── seeds.py                  # Database seeder (creates default users & demo lots)
│
├── docs/                         # Documentation & assets
│   └── screenshots/              # High-resolution platform previews
│
├── static/                       # Static stylesheets, brand media & scripts
│   ├── css/style.css             # Main unified stylesheet (responsive & cleaned)
│   ├── js/                       # Client-side JavaScript helpers
│   └── img/                      # Official platform logos and markers
│
├── templates/                    # Cleaned, responsive HTML templates
│   ├── accounts/                 # Driver login, register, profile
│   ├── admin_panel/              # Admin dashboard, pricing, payments, complaints
│   ├── lot_owner_panel/          # Owner dashboard, slots, earnings, extensions
│   ├── parking/                  # Home search, lot detail, booking, ticket pass
│   └── base.html                 # Unified master layout
│
├── .env.example                  # Environment credentials template
├── .gitignore                    # Production Git ignore rules
├── LICENSE                       # MIT Open-Source License
├── manage.py                     # Django CLI management executable
├── README.md                     # Comprehensive project documentation
└── requirements.txt              # Pinned Python package dependencies
```

## 🛡️ License

This project is licensed under the [MIT License](LICENSE).
