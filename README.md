# 🌾 Shetkari-Kamgar (Labor Marketplace)

A comprehensive, bilingual (English/Marathi) web application designed to bridge the gap between farmers and agricultural workers in Maharashtra, India. Built with Spring Boot, PostgreSQL, and modern web technologies, featuring a robust SaaS subscription model and a powerful Admin Control Panel.

---

## 📋 Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Architecture & APIs](#architecture--apis)
- [Monetization Model](#monetization-model)
- [Future Enhancements](#future-enhancements)
- [License](#license)

---

## ✨ Features

### 👑 Super Admin Control Panel
- **Comprehensive Dashboard:** Live statistics on total users, active posts, pending issues, premium users, and estimated revenue.
- **User Management:** View detailed user profiles, check subscription statuses, temporarily ban rule-breakers, or permanently delete accounts.
- **Grievance System:** Review and resolve user complaints (e.g., fake profiles, payment issues) with one click.
- **Dynamic Database Management:** Add new States, Districts, and Villages directly from the dashboard with duplicate-prevention constraints.
- **Export Data:** Generate and download complete system reports as CSV files for offline analysis.

### 💎 Premium Subscription Model (SaaS)
- **Freemium Tier:** Free users are strictly limited to 1 active job/availability post to test the platform.
- **Premium Tier (₹99/month):** Unlocks unlimited posting capabilities and adds a verified "Premium" badge to the user's profile.
- **Simulated Payment Gateway:** Includes a fully animated mock UPI payment gateway modal, ready to be swapped out for Razorpay or Stripe.

### 📍 Smart Dynamic Locations
- **Hierarchical Dropdowns:** State ➔ District ➔ Village dynamic loading via asynchronous REST APIs.
- **Fast Loading:** Backend only sends necessary data, drastically reducing load times during registration and job posting.
- **Pre-loaded Database:** Comes with 90+ pre-configured towns and villages across Sangli, Satara, and Kolhapur.

### 🔐 Advanced Security & Profiles
- **Profile Management:** Users can update their personal details and active locations.
- **Secure Password Resets:** Built-in password change functionality that strictly verifies the old BCrypt-hashed password before allowing updates.
- **Anti-Lockout Logic:** Admins are programmatically prevented from accidentally banning or deleting their own accounts.

### 💼 Core Job/Worker Matchmaking
- **For Farmers:** Post detailed jobs (wage, needed workers, skills, dates), review applicants, mark jobs as "Full", and delete old history.
- **For Workers:** Post availability, browse local jobs, apply with one click, and track application statuses via a live notification bell.

### 🌐 Localization (i18n)
- **Bilingual Support:** Instant toggling between English and Marathi via client-side translation scripts.
- **Persistent Preferences:** User language choice is saved in `localStorage` across sessions.

---

## 🛠️ Tech Stack

### Backend
- **Java 17+** - **Spring Boot 3.2.0** (Web, Data JPA, Security)
- **PostgreSQL 12+** (Relational Database)
- **Maven** (Build Tool)

### Frontend
- **HTML5 & CSS3** (Custom agriculture-themed UI)
- **JavaScript (ES6+)** (Async API fetching, animations, dynamic DOM manipulation)
- **Bootstrap 5.3.2** (Responsive layout & Modals)
- **Bootstrap Icons 1.11.1**
- **Thymeleaf** (Server-side template rendering)

---

## 📁 Project Structure


```

labor/
├── src/
│   ├── main/
│   │   ├── java/com/labor/
│   │   │   ├── LaborApplication.java          # Main app entry
│   │   │   ├── DataLoader.java                # Auto-generates Admin & Towns
│   │   │   ├── config/
│   │   │   │   └── SecurityConfig.java        # Route protection & BCrypt
│   │   │   ├── controller/
│   │   │   │   ├── AdminController.java       # Admin dashboard & management
│   │   │   │   ├── LocationApiController.java # Dynamic State/District APIs
│   │   │   │   ├── SubscriptionController.java# Upgrades & mock payments
│   │   │   │   └── UserController.java        # Core auth, posts, and profiles
│   │   │   ├── model/
│   │   │   │   ├── User.java                  # Includes Subscription & Ban flags
│   │   │   │   ├── JobPost.java

│   │   │   │   ├── Complaint.java             # Grievance entity
│   │   │   │   └── Town.java                  # State/District/Village entity
│   │   │   ├── repository/                    # Spring Data JPA Interfaces
│   │   │   └── service/
│   │   │       └── CustomUserDetailsService.java
│   │   └── resources/
│   │       ├── application.properties         # Server/DB config (Port 8081)
│   │       └── templates/
│   │           ├── admin_dashboard.html       # Super Admin UI
│   │           ├── pricing.html               # Subscription plans & Gateway
│   │           ├── profile.html               # User details & Password update
│   │           ├── register.html              # Dynamic location registration
│   │           ├── worker_feed.html           # Worker UI
│   │           ├── farmer_dashboard.html      # Farmer UI
│   │           └── translations.js            # i18n Dictionary
└── pom.xml                                    # Dependencies

```

---

## 🚀 Quick Start

### 1. Database Setup
Ensure PostgreSQL is running and create the database:
```sql
CREATE DATABASE labor_marketplace;
CREATE USER labor_user WITH PASSWORD 'labor_password_123';
GRANT ALL PRIVILEGES ON DATABASE labor_marketplace TO labor_user;

```

### 2. Build & Run

```bash
mvn clean compile
mvn spring-boot:run

```

### 3. Access Application

Open browser and navigate to: **http://localhost:8081**

### 4. Default Admin Login

The `DataLoader` automatically creates an untouchable Super Admin on first boot:

* **Mobile Number:** `9999999999`
* **Password:** `admin123`

---

## ⚙️ Configuration

File: `src/main/resources/application.properties`

```properties
# Server
server.port=8081

# Database
spring.datasource.url=jdbc:postgresql://localhost:5432/labor_marketplace
spring.datasource.username=labor_user
spring.datasource.password=labor_password_123

# JPA/Hibernate
spring.jpa.hibernate.ddl-auto=update
spring.jpa.show-sql=false

```

---

## 🔌 Core API Endpoints

### Public Endpoints

* `GET /api/locations/states` - Returns unique states
* `GET /api/locations/districts?state={state}` - Returns districts for a state
* `GET /api/locations/towns?state={state}&district={district}` - Returns specific villages

### User & Post Routes (Protected)

* `POST /post-job` - Validates subscription limit before posting
* `POST /post-availability` - Validates subscription limit before posting
* `POST /profile/update` - Modifies core details
* `POST /profile/change-password` - BCrypt validation and update

### Admin Routes (Role: ADMIN)

* `GET /admin/dashboard` - Fetches massive data aggregation
* `POST /admin/toggle-ban` - Flips `isBanned` boolean
* `POST /admin/delete-user` - Cascading deletion of user and related entities
* `POST /admin/add-town` - Adds location with duplicate prevention

---

## 💎 Monetization Model

The application utilizes a **SaaS (Software as a Service)** approach to generate revenue.

1. **Free Tier:** Users are restricted to maintaining exactly **1 active post** in the database at any given time. Attempting to post a second job automatically triggers a redirect to the `/pricing` page.
2. **Premium Tier:** Upgrading updates the database `subscriptionPlan` to `PREMIUM` and sets a `subscriptionEndDate` 30 days in the future, bypassing all limits and injecting Premium UI badges.

---

## 📈 Future Enhancements

* [ ] **Live Payment Gateway Integration:** Replace the mock JS timeout in `pricing.html` with Razorpay or Stripe Webhooks.
* [ ] **WhatsApp API Integration:** Use Twilio to send automated WhatsApp messages when a worker applies for a job.
* [ ] **AI Wage Predictor:** Integrate a Python/Flask microservice to analyze local data and suggest "Fair Market Wages" to farmers.
* [ ] **Machine Learning Matchmaking:** Recommend specific jobs to workers based on their historical application data.

---

## 👨‍💻 Author

**Indrajeet Pawar** *Master of Computer Applications (MCA) | Full Stack Developer*
Created to empower the agricultural workforce of Maharashtra.

---

## 📄 License

This project is proprietary and intended for educational and portfolio purposes.

Last Updated: March 2026

```

```
