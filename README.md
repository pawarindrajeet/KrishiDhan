🌾 KrishiDhan (Smart Farming Web Application)
A comprehensive, AI-powered web application designed to empower Indian farmers with technology, market access, and scientific knowledge. Built with Python, Flask, and PostgreSQL, KrishiDhan integrates an e-commerce platform for agricultural supplies, real-time market trends, and an intelligent Plant Doctor module for crop disease detection.

📋 Table of Contents
Features

Tech Stack

Project Structure

Prerequisites

Quick Start

Configuration

Architecture & Routes

Future Enhancements

License

✨ Features
👑 Admin Control Panel
Shop Management: Add, edit, and delete agricultural products (seeds, fertilizers, pesticides) dynamically using SQLAlchemy ORM.

Farmer Activity Tracking: Monitor recent e-commerce orders and track which crops farmers are actively growing.

Market Price Updates: Manually input and update daily market prices per quintal for various crops across different states and districts.

Database Oversight: Manage registered farmers and core crop category data.

🩺 AI Plant Doctor
Image Upload: Farmers can upload photos of crop leaves directly from their devices.

Disease Detection: Analyzes the leaf to identify diseases (e.g., Late Blight) and provides a health status/confidence score.

Actionable Cures: Recommends specific treatments and pesticides based on the diagnosed issue.

🛒 Dynamic E-Commerce Shop
Farmer Marketplace: Browse categorized agricultural supplies with real-time stock availability.

Smart Cart System: Add items to a dynamic cart that calculates quantities and grand totals using raw SQL joins.

Order Processing: Seamless checkout experience that automatically updates product inventory and logs the order history.

📊 Smart Dashboards & Analytics
Live Weather Integration: Fetches real-time temperature, humidity, and conditions based on the farmer's registered district using the OpenWeather API.

Market Trends: Visualizes historical market prices for major crops (Wheat, Rice, Cotton) using dynamic charts and JSON data handling.

Agriculture News & Schemes: Pulls live national agricultural news using the NewsAPI and displays core government schemes (PMFBY, PM-KISAN, KCC).

🔐 Secure Authentication & Profiles
Role-Based Access: Distinct routing and dashboards for admin and farmer roles.

Session Management: Secure Flask sessions ensure users can only access their specific data and cart.

🛠️ Tech Stack
Backend
Python 3.13+

Flask (Web Framework, Routing, Session Management)

PostgreSQL 12+ (Relational Database)

SQLAlchemy & psycopg2 (Hybrid ORM and Raw SQL database interaction)

Frontend
HTML5 & CSS3 (Custom agricultural UI)

JavaScript (ES6+) (Dynamic charting and API handling)

Jinja2 (Server-side template rendering)

External APIs
OpenWeather API (Live local weather)

NewsAPI (Live agriculture updates)

📁 Project Structure
Plaintext
KrishiDhan/
├── app.py                     # Main application entry, routing, and logic
├── config.py                  # Environment configurations
├── requirements.txt           # Python dependencies
├── database/
│   └── db_setup.sql           # Raw SQL script for core table creation
├── static/
│   ├── css/
│   │   └── style.css          # Global styling
│   └── images/
│       ├── crops/             # Uploaded crop visuals
│       ├── products/          # Shop inventory images
│       └── uploads/leaves/    # User-uploaded leaves for AI analysis
└── templates/
    ├── admin/                 # Admin dashboard, shop management, and activity views
    ├── common/
    │   └── footer.html        # Reusable UI components
    ├── farmer/                # Farmer dashboard, cart, shop, and Plant Doctor views
    └── home/                  # Public landing page, registration, and login
🚀 Quick Start
1. Database Setup
Ensure PostgreSQL is running on your machine (localhost:5432).

Open pgAdmin or SQL Shell.

Create the database: CREATE DATABASE krishidhan_db;

Run the raw SQL queries found in database/db_setup.sql to generate the core tables (users, crops, cart, etc.).

2. Virtual Environment & Dependencies
Open your terminal in the project root directory:

PowerShell
# Create virtual environment
python -m venv .venv

# Activate it (Windows)
.\.venv\Scripts\Activate.ps1

# Install required packages
pip install Flask psycopg2-binary Flask-SQLAlchemy requests numpy
3. Generate ORM Tables
Open the Python shell to let SQLAlchemy generate the shop tables:

Python
python
>>> from app import app, db
>>> app.app_context().push()
>>> db.create_all()
>>> exit()
4. Run the Application
PowerShell
python app.py
Open your browser and navigate to: http://127.0.0.1:5000

⚙️ Configuration
Database and API configurations are managed directly in app.py and config.py.

Ensure your PostgreSQL credentials match the URI in app.py:

Python
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:YOUR_PASSWORD@localhost:5432/krishidhan_db'
🔌 Core Architecture & Routes
Public Endpoints
GET / - Landing page with weather search widget.

GET, POST /login - Dual authentication for Farmers and Admins.

GET, POST /register - Farmer onboarding.

Farmer Routes (Protected)
GET /farmer_dashboard - Overview with localized weather API fetch.

GET /shop - Renders SQLAlchemy Product models.

POST /add_to_cart/<id> - Updates cart table via psycopg2.

GET, POST /plant_doctor - Handles image upload and mock AI prediction.

Admin Routes (Protected)
GET, POST /add_product - Inserts new items into the dynamic shop.

GET /farmer_activity - Joins users, orders, and farmer_crops tables for oversight.

📈 Future Enhancements
[ ] Real Machine Learning Integration: Replace the randomized Plant Doctor logic with a trained .pkl TensorFlow/Keras model for actual image classification.

[ ] Payment Gateway Integration: Upgrade the shop checkout system using Razorpay or Stripe APIs for real transactions.

[ ] SMS/WhatsApp Alerts: Integrate Twilio to send farmers automated alerts about extreme weather or market price spikes.

[ ] Crop Yield Prediction: Build a predictive model utilizing soil type, weather history, and crop data to forecast harvest yields.

👨‍💻 Author
Indrajeet Pawar Master of Computer Applications (MCA) | Full Stack Developer Empowering Indian farmers with technology, market access, and scientific knowledge.

📄 License
This project is proprietary and intended for educational and portfolio purposes.
