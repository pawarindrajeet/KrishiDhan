from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import psycopg2
import os
from werkzeug.utils import secure_filename
from config import Config
import random
import pickle
import numpy as np
import requests  # Required for Weather API
import json 
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy # ✅ NEW: Required for Dynamic Shop

app = Flask(__name__)
app.secret_key = 'super_secret_key'
app.secret_key = 'krishidhan_secret_key' 
app.config.from_object(Config)

# --- 1. DATABASE CONFIGURATION (PostgreSQL via SQLAlchemy) ---
# ✅ CHANGE: Replace '1234' with your actual PostgreSQL password if different
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:Admin@localhost:5432/krishidhan_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app) # Initialize ORM

# --- 2. DATABASE MODELS (For Shop System) ---
# These link to your existing PostgreSQL tables automatically

class Product(db.Model):
    __tablename__ = 'products' # Links to your existing table
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    image = db.Column(db.String(100), nullable=True) # Matches your DB column 'image_url' or 'image'? 
    # Note: In your raw SQL you used 'image_url'. I will map it below.
    image_url = db.Column('image_url', db.String(100), nullable=True) 

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    product_name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)

# Image Upload Configuration
UPLOAD_FOLDER = 'static/images/products' # Updated to products folder
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True) 

# --- HELPER: RAW DB CONNECTION (For Login/Register/Crops) ---
# We keep this for your existing logic that relies on it.
def get_db_connection():
    conn = psycopg2.connect(
        host=app.config['DB_HOST'],
        database=app.config['DB_NAME'],
        user=app.config['DB_USER'],
        password=app.config['DB_PASS']
    )
    return conn

# --- AUTOMATIC CART COUNT FOR ALL PAGES ---
@app.context_processor
def inject_cart_count():
    if 'user_id' in session:
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM cart WHERE user_id = %s", (session['user_id'],))
            count = cur.fetchone()[0]
            cur.close()
            conn.close()
            return dict(cart_count=count)
        except Exception as e:
            return dict(cart_count=0)
    return dict(cart_count=0)

# --- HOME & AUTHENTICATION ROUTES ---

@app.route('/', methods=['GET', 'POST'])
def home():
    if 'user_id' in session:
        if session.get('role') == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('farmer_dashboard'))

    city = "Pune"
    weather_data = None
    
    if request.method == 'POST':
        city = request.form.get('city')

    api_key = "5cfe4db720b5f2323518e5b321fa3719" 
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"

    try:
        response = requests.get(url)
        if response.status_code == 200:
            weather_data = response.json()
    except Exception as e:
        print("Weather Connection Error:", e)

    return render_template('home/index.html', weather=weather_data, city=city)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form['full_name']
        mobile = request.form['mobile']
        email = request.form['email']
        password = request.form['password']
        state = request.form['state']
        district = request.form['district']
        role = 'farmer' 

        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO users (full_name, mobile, email, password, role, state, district)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (full_name, mobile, email, password, role, state, district))
            conn.commit()
            cur.close()
            conn.close()
            flash("Registration Successful! Please Login.", "success")
            return redirect(url_for('login'))
        except Exception as e:
            flash(f"Error: {e}", "error")
            return f"Error: {e}"
    return render_template('home/register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form['identifier']
        password = request.form['password']

        conn = get_db_connection()
        cur = conn.cursor()
        
        # Check User
        cur.execute("SELECT * FROM users WHERE (mobile = %s OR email = %s) AND password = %s", (identifier, identifier, password))
        user = cur.fetchone()
        
        # Check Admin
        cur.execute("SELECT * FROM admins WHERE username = %s AND password = %s", (identifier, password))
        admin = cur.fetchone()
        
        cur.close()
        conn.close()

        if user:
            session['user_id'] = user[0]
            session['role'] = 'farmer'
            session['name'] = user[1]
            return redirect(url_for('farmer_dashboard'))
            
        elif admin:
            session['user_id'] = admin[0]
            session['role'] = 'admin'
            return redirect(url_for('admin_dashboard'))
            
        else:
            flash("❌ Invalid Credentials! Please check your Farmer_ID or Password.", "error")
            return redirect(url_for('home'))

    return render_template('home/login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


# --- DASHBOARD ROUTES ---

@app.route('/admin_dashboard')
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    return render_template('admin/dashboard.html')

@app.route('/farmer_dashboard')
def farmer_dashboard():
    if 'user_id' not in session: return redirect(url_for('login'))
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT full_name, mobile, state, district FROM users WHERE id = %s", (session['user_id'],))
    user = cur.fetchone()
    cur.close()
    conn.close()

    weather_data = None
    if user:
        district = user[3]
        api_key = "5cfe4db720b5f2323518e5b321fa3719" 
        url = f"http://api.openweathermap.org/data/2.5/weather?q={district}&appid={api_key}&units=metric"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                weather_data = response.json()
        except Exception as e:
            print("Connection Error:", e)

    return render_template('farmer/dashboard.html', user=user, weather=weather_data)


# --- SECURE CROP ROUTES ---

@app.route('/crops')
def crop_categories():
    if 'user_id' not in session: return redirect(url_for('login'))
    return render_template('farmer/crop_categories.html')

@app.route('/crops/<category_name>')
def show_crops_by_category(category_name):
    if 'user_id' not in session: return redirect(url_for('login'))
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM crops WHERE category = %s", (category_name,))
    crops = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('farmer/crop_list.html', crops=crops, category_name=category_name)

@app.route('/crop_details/<int:crop_id>')
def crop_details(crop_id):
    if 'user_id' not in session: return redirect(url_for('login'))
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM crops WHERE id = %s", (crop_id,))
    crop = cur.fetchone()
    cur.close()
    conn.close()
    return render_template('farmer/crop_detail_view.html', crop=crop)


# --- SHOP & CART ROUTES (Updated with Quantity Logic) ---

# 1. ADD TO CART (With Quantity Support)
@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    if 'user_id' not in session: return redirect(url_for('login'))

    user_id = session['user_id']
    quantity = int(request.form.get('quantity', 1))

    conn = get_db_connection()
    cur = conn.cursor()

    # Check existence
    cur.execute("SELECT quantity FROM cart WHERE user_id = %s AND product_id = %s", (user_id, product_id))
    existing_item = cur.fetchone()

    if existing_item:
        new_quantity = existing_item[0] + quantity
        cur.execute("UPDATE cart SET quantity = %s WHERE user_id = %s AND product_id = %s", 
                    (new_quantity, user_id, product_id))
    else:
        cur.execute("INSERT INTO cart (user_id, product_id, quantity) VALUES (%s, %s, %s)", 
                    (user_id, product_id, quantity))

    conn.commit()
    cur.close()
    conn.close()

    # 🔔 THIS IS THE NEW LINE FOR THE POPUP
    flash(f"✅ Added {quantity} item(s) to your cart!", "success")
    
    return redirect(url_for('shop'))


# 2. VIEW CART (Calculates Totals)
@app.route('/cart')
def cart():
    if 'user_id' not in session: return redirect(url_for('login'))
    
    user_id = session['user_id']
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Get Product Details + Cart Quantity
    # We calculate Total Price (Price * Quantity) directly in SQL
    cur.execute("""
        SELECT c.id, p.name, p.category, p.price, p.image_url, c.quantity, (p.price * c.quantity) as item_total
        FROM cart c
        JOIN products p ON c.product_id = p.id
        WHERE c.user_id = %s
        ORDER BY c.id DESC
    """, (user_id,))
    
    cart_items = cur.fetchall()
    
    # Calculate Grand Total (Sum of all item totals)
    grand_total = sum(item[6] for item in cart_items) if cart_items else 0
    
    cur.close()
    conn.close()
    
    return render_template('farmer/cart.html', cart_items=cart_items, grand_total=grand_total)


# 3. REMOVE FROM CART
@app.route('/remove_from_cart/<int:cart_id>')
def remove_from_cart(cart_id):
    if 'user_id' not in session: 
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM cart WHERE id = %s", (cart_id,))
    conn.commit()
    cur.close()
    conn.close()
    
    return redirect(url_for('cart'))


# --- ADMIN: MANAGEMENT ROUTES ---

@app.route('/add_crop', methods=['GET', 'POST'])
def add_crop():
    if session.get('role') != 'admin': return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name']
        category = request.form['category']
        soil_type = request.form['soil_type']
        description = request.form['description']
        file = request.files['image']
        
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join('static/images/crops', filename)) # Save to crops folder
            
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO crops (name, category, image_url, soil_type, description)
                VALUES (%s, %s, %s, %s, %s)
            """, (name, category, filename, soil_type, description))
            conn.commit()
            cur.close()
            conn.close()
            return redirect(url_for('admin_dashboard'))

    return render_template('admin/add_crop.html')

@app.route('/manage_farmers')
def manage_farmers():
    if session.get('role') != 'admin': return redirect(url_for('login'))
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, full_name, mobile, state, district FROM users")
    farmers = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('admin/manage_farmers.html', farmers=farmers)

@app.route('/update_price', methods=['GET', 'POST'])
def update_price():
    if session.get('role') != 'admin': return redirect(url_for('login'))
    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        crop_id = request.form['crop_id']
        state = request.form['state']
        district = request.form['district']
        price = request.form['price']
        cur.execute("""
            INSERT INTO market_prices (crop_id, state, district, price_per_quintal)
            VALUES (%s, %s, %s, %s)
        """, (crop_id, state, district, price))
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for('admin_dashboard'))

    cur.execute("SELECT id, name, category FROM crops")
    crops = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('admin/market_price.html', crops=crops)


# --- FARMER: PLANT DOCTOR ---
@app.route('/plant_doctor', methods=['GET', 'POST'])
def plant_doctor():
    if 'user_id' not in session: return redirect(url_for('login'))
    prediction = None
    image_url = None

    if request.method == 'POST':
        if 'leaf_image' not in request.files: return redirect(request.url)
        file = request.files['leaf_image']
        if file.filename == '': return redirect(request.url)

        if file:
            filename = secure_filename(file.filename)
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], 'leaves', filename)
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            file.save(save_path)
            image_url = "uploads/leaves/" + filename

            diseases = [
                {"name": "Late Blight (Fungal)", "status": "Danger 🔴", "cure": "Spray Mancozeb.", "confidence": "94%"},
                {"name": "Healthy Plant", "status": "Safe 🟢", "cure": "No action needed.", "confidence": "99%"}
            ]
            prediction = random.choice(diseases)

    return render_template('farmer/plant_doctor.html', prediction=prediction, image_url=image_url)


# --- PUBLIC ROUTES ---
@app.route('/market')
def market_view():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT mp.id, c.name, c.category, mp.state, mp.district, mp.price_per_quintal, mp.date
        FROM market_prices mp JOIN crops c ON mp.crop_id = c.id ORDER BY mp.date DESC
    """)
    prices = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('home/market.html', prices=prices)

@app.route('/weather', methods=['GET', 'POST'])
def weather():
    city = "Pune"
    if request.method == 'POST': city = request.form.get('city')
    weather_data = {'temp': 28, 'humidity': 60, 'wind': 10, 'desc': 'Sunny ☀️'}
    return render_template('home/weather.html', weather=weather_data, city=city)

# ✅ KEEP THIS NEW VERSION ONLY
@app.route('/news_schemes')
def news_schemes():
    # 1. FETCH LIVE NEWS (API)
    api_key = "cef4263381c9470e8ec5a5848e88e2ff"
    url = f"https://newsapi.org/v2/everything?q=agriculture+india&sortBy=publishedAt&language=en&apiKey={api_key}"
    
    updates = []
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            updates = resp.json().get('articles', [])[:6]
    except Exception as e:
        print("News API Error:", e)

    # 2. DEFINE SCHEMES (Static Data)
    core_schemes = [
        {"title": "Pradhan Mantri Fasal Bima Yojana", "description": "Crop insurance scheme to provide financial support.", "link": "https://pmfby.gov.in/", "icon": "🛡️"},
        {"title": "PM-KISAN Samman Nidhi", "description": "Financial benefit of ₹6,000 per year for farmers.", "link": "https://pmkisan.gov.in/", "icon": "💰"},
        {"title": "Kisan Credit Card (KCC)", "description": "Access to affordable credit for farmers.", "link": "https://www.myscheme.gov.in/schemes/kcc", "icon": "💳"}
    ]

    # 3. SMART RENDER (Check if user is logged in)
    if 'user_id' in session:
        # If Farmer -> Show Dashboard Layout
        return render_template('farmer/news_schemes.html', updates=updates, schemes=core_schemes)
    else:
        # If Guest -> Show Home Layout (Public)
        return render_template('home/news.html', updates=updates, schemes=core_schemes)

# ✅ ANALYTICS ROUTE (Backend Logic)
@app.route('/analytics')
def analytics():
    if 'user_id' not in session: return redirect(url_for('login'))
    
    # 1. Define Data (This is Python sending data to your graph!)
    months_list = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul']
    wheat_prices = [2100, 2150, 2200, 2180, 2250, 2300, 2400]
    rice_prices = [1900, 1850, 1880, 1920, 1950, 1980, 2000]
    cotton_prices = [5500, 5600, 5400, 5700, 5900, 6100, 6200]
    
    # 2. Pass Data to Template
    return render_template('farmer/analytics.html',
                           months=json.dumps(months_list),
                           wheat=json.dumps(wheat_prices),
                           rice=json.dumps(rice_prices),
                           cotton=json.dumps(cotton_prices))

@app.route('/recommend', methods=['GET', 'POST'])
def recommend():
    if 'user_id' not in session: return redirect(url_for('login'))
    prediction = None
    if request.method == 'POST':
        prediction = "Rice (Smart Prediction)"
    return render_template('farmer/recommend.html', prediction=prediction)

@app.route('/profile')
def profile():
    user_id = session.get('user_id')
    if not user_id: return redirect(url_for('login'))
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, full_name, mobile, state, district FROM users WHERE id = %s", (user_id,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return render_template('farmer/profile.html', user=user)


# --- FARMER: MY CROPS ---
@app.route('/my_crops')
def my_crops():
    if 'user_id' not in session: return redirect(url_for('login'))
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM farmer_crops WHERE user_id = %s ORDER BY sown_date DESC", (session['user_id'],))
    crops = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('farmer/my_crops.html', crops=crops)

@app.route('/add_my_crop', methods=['POST'])
def add_my_crop():
    if 'user_id' not in session: return redirect(url_for('login'))
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO farmer_crops (user_id, crop_name, sown_date, status, next_action) VALUES (%s, %s, %s, %s, %s)",
                (session['user_id'], request.form['crop_name'], request.form['sown_date'], request.form['status'], request.form['next_action']))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('my_crops'))

@app.route('/delete_my_crop/<int:id>')
def delete_my_crop(id):
    if 'user_id' not in session: return redirect(url_for('login'))
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM farmer_crops WHERE id = %s AND user_id = %s", (id, session['user_id']))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('my_crops'))

@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


# --- 🛒 ADMIN & FARMER SHOP SYSTEM (UPDATED WITH ORM) ---

# ✅ 1. ADD PRODUCT (Updated to use ORM)
@app.route('/add_product', methods=['GET', 'POST'])
def add_product_orm(): # Renamed slightly to avoid conflict if you kept old function
    if session.get('role') != 'admin': return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name']
        category = request.form['category']
        price = float(request.form['price'])
        # Add stock logic if your form has it, otherwise default
        stock = int(request.form.get('stock', 100)) 
        
        file = request.files['image']
        filename = 'default_product.png'
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Use SQLAlchemy to Add
        new_product = Product(name=name, category=category, price=price, stock=stock, image_url=filename)
        db.session.add(new_product)
        db.session.commit()
        flash("Product Added to Shop!", "success")
        return redirect(url_for('manage_shop'))

    return render_template('admin/add_product.html')

# ✅ 2. FARMER SHOP ROUTE (Final Version)
# ✅ KEEP THIS NEW SECTION ONLY
# ✅ FARMER SHOP ROUTE (Fixed)
@app.route('/shop')
def shop():
    if 'user_id' not in session: 
        return redirect(url_for('login'))
    
    # 1. Fetch Products
    products = Product.query.order_by(Product.id.desc()).all()
    
    # 2. Calculate Cart Count
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM cart WHERE user_id = %s", (session['user_id'],))
    result = cur.fetchone()
    cart_count = result[0] if result else 0
    cur.close()
    conn.close()
    
    # 3. Render Page
    return render_template('farmer/shop.html', products=products, cart_count=cart_count)


# ✅ 3. MANAGE SHOP (Updated to use ORM)
@app.route('/manage_shop', methods=['GET', 'POST'])
def manage_shop():
    if session.get('role') != 'admin': return redirect(url_for('login'))
    
    # If POST, it's adding a product (Reusing the logic from add_product or handling here)
    if request.method == 'POST':
        return add_product_orm() # Redirect to the ORM logic above

    products = Product.query.order_by(Product.id.desc()).all()
    return render_template('admin/manage_shop.html', products=products)

# ✅ 4. BUY NOW (NEW: Updates Stock)
@app.route('/buy_now/<int:id>')
def buy_now(id):
    if 'user_id' not in session: return redirect(url_for('login'))
    
    product = Product.query.get(id)
    if product and product.stock > 0:
        # 1. Decrease Stock
        product.stock -= 1
        
        # 2. Save Order
        new_order = Order(user_id=session['user_id'], product_name=product.name, price=product.price)
        db.session.add(new_order)
        
        db.session.commit()
        flash(f"Successfully bought {product.name}!", "success")
    else:
        flash("Out of Stock!", "danger")
        
    return redirect(url_for('shop'))

# ✅ 5. DELETE PRODUCT (Updated to use ORM)
@app.route('/delete_product/<int:id>')
def delete_product_orm(id):
    if session.get('role') != 'admin': return redirect(url_for('login'))
    
    product = Product.query.get(id)
    if product:
        db.session.delete(product)
        db.session.commit()
        flash("Product Deleted!", "danger")
        
    return redirect(url_for('manage_shop'))


# --- OTHER FEATURES ---
# ✅ CORRECTED: Put the logic directly inside the function

# --- ADMIN: FARMER ACTIVITY (Restored Logic) ---
@app.route('/farmer_activity')
def farmer_activity():
    if session.get('role') != 'admin': return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()

    # 1. Fetch Recent Orders (Who bought what?)
    cur.execute("""
        SELECT o.id, u.full_name, o.product_name, o.price, o.order_date 
        FROM orders o
        JOIN users u ON o.user_id = u.id
        ORDER BY o.order_date DESC
    """)
    orders = cur.fetchall()

    # 2. Fetch Active Crops (Who is growing what?)
    cur.execute("""
        SELECT fc.id, u.full_name, fc.crop_name, fc.status, fc.sown_date 
        FROM farmer_crops fc
        JOIN users u ON fc.user_id = u.id
        ORDER BY fc.sown_date DESC
    """)
    crops = cur.fetchall()

    cur.close()
    conn.close()
    return render_template('admin/farmer_activity.html', orders=orders, crops=crops)


# --- CHECKOUT (Restored Logic) ---
@app.route('/checkout')
def checkout():
    if 'user_id' not in session: return redirect(url_for('login'))

    user_id = session['user_id']
    conn = get_db_connection()
    cur = conn.cursor()

    # 1. Move items from Cart to Orders table
    # We join Cart with Products to get the name and price dynamically
    cur.execute("""
        INSERT INTO orders (user_id, product_name, price)
        SELECT c.user_id, p.name, p.price
        FROM cart c
        JOIN products p ON c.product_id = p.id
        WHERE c.user_id = %s
    """, (user_id,))

    # 2. Clear the Cart for this user
    cur.execute("DELETE FROM cart WHERE user_id = %s", (user_id,))
    
    conn.commit()
    cur.close()
    conn.close()
    
    return render_template('farmer/order_success.html')


@app.route('/insurance_calculator')
def insurance_calculator():
    if 'user_id' not in session: return redirect(url_for('login'))
    return render_template('farmer/insurance.html')

@app.route('/calculator')
def calculator():
    return render_template('home/calculator.html')

if __name__ == '__main__':
    app.run(debug=True)