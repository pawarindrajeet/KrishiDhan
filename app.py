# ==========================================
# KRISHIDHAN - MAIN FLASK APPLICATION
# ==========================================

import os
import json
import random
import pickle
import numpy as np
import requests
import psycopg2
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from config import Config

import tensorflow as tf
from tensorflow.keras.preprocessing.image import load_img, img_to_array
from PIL import Image

# ==========================================
# 1. APP CONFIGURATION & SETUP
# ==========================================
app = Flask(__name__)
app.secret_key = 'krishidhan_enterprise_secret' # Unified secret key
app.config.from_object(Config)

# Database Configuration (SQLAlchemy for Shop, Raw psycopg2 for Legacy features)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:Admin@localhost:5432/krishidhan_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# File Upload Configuration
UPLOAD_FOLDER = 'static/images/products'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('static/images/crops', exist_ok=True)
os.makedirs('static/images/leaves', exist_ok=True)


# ==========================================
# 2. DATABASE MODELS (SQLAlchemy ORM)
# ==========================================
class Product(db.Model):
    __tablename__ = 'products' 
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    image_url = db.Column(db.String(100), nullable=True)
    
class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    product_name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)


# ==========================================
# 3. HELPER FUNCTIONS & MACHINE LEARNING
# ==========================================
def get_db_connection():
    """Returns a raw psycopg2 database connection."""
    conn = psycopg2.connect(
        host=app.config['DB_HOST'],
        database=app.config['DB_NAME'],
        user=app.config['DB_USER'],
        password=app.config['DB_PASS']
    )
    return conn

@app.context_processor
def inject_cart_count():
    """Automatically injects the user's cart count into every HTML template."""
    if 'user_id' in session:
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM cart WHERE user_id = %s", (session['user_id'],))
            count = cur.fetchone()[0]
            cur.close()
            conn.close()
            return dict(cart_count=count)
        except Exception:
            return dict(cart_count=0)
    return dict(cart_count=0)

@app.after_request
def add_header(response):
    """Prevents caching of sensitive pages after logout."""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# ---- LOAD ML MODELS GLOBALLY ----

# 1. Load Crop Recommender (Tabular ML)
try:
    with open('crop_model.pkl', 'rb') as file:
        crop_model = pickle.load(file)
    print("✅ AI Crop Model Loaded Successfully.")
except Exception as e:
    print("⚠️ Warning: crop_model.pkl not found. Run train_model.py first!")
    crop_model = None

# 2. Load Plant Doctor (Deep Learning CNN)
try:
    plant_model = tf.keras.models.load_model('plant_doctor.h5')
    print("✅ Deep Learning Plant Doctor Model Loaded.")
except Exception as e:
    print("⚠️ Warning: plant_doctor.h5 not found. Run train_cnn.py first!")
    plant_model = None

# Plant Disease Dictionary
DISEASE_INFO = {
    0: {"name": "Healthy Plant", "status": "Safe 🟢", "cure": "Keep up the good work! Maintain regular watering and nutrient balance."},
    1: {"name": "Late Blight (Fungal)", "status": "Danger 🔴", "cure": "Apply Mancozeb or Copper Fungicide. Remove infected leaves immediately to prevent spreading."},
    2: {"name": "Leaf Rust", "status": "Danger 🔴", "cure": "Spray Neem oil or sulfur-based fungicide. Improve air circulation around the crops."},
    3: {"name": "Powdery Mildew", "status": "Danger 🔴", "cure": "Spray a mixture of baking soda and water. Prune heavily affected areas."}
}


# ==========================================
# 4. AUTHENTICATION & CORE ROUTES
# ==========================================
@app.route('/', methods=['GET', 'POST'])
def home():
    if 'user_id' in session:
        return redirect(url_for('admin_dashboard')) if session.get('role') == 'admin' else redirect(url_for('farmer_dashboard'))

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
            flash("❌ Invalid Credentials! Please check your Farmer ID or Password.", "error")
            return redirect(url_for('home'))

    return render_template('home/login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Successfully logged out.", "success")
    return redirect(url_for('home'))


# ==========================================
# 5. ADMIN CONTROL CENTER ROUTES
# ==========================================
@app.route('/admin_dashboard')
def admin_dashboard():
    if session.get('role') != 'admin': return redirect(url_for('login'))
    return render_template('admin/dashboard.html')

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
            file.save(os.path.join('static/images/crops', filename))
            
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO crops (name, category, image_url, soil_type, description)
                VALUES (%s, %s, %s, %s, %s)
            """, (name, category, filename, soil_type, description))
            conn.commit()
            cur.close()
            conn.close()
            flash("Crop added successfully to database.", "success")
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
        flash("Mandi price updated successfully.", "success")
        return redirect(url_for('admin_dashboard'))

    cur.execute("SELECT id, name, category FROM crops")
    crops = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('admin/market_price.html', crops=crops)

@app.route('/farmer_activity')
def farmer_activity():
    if session.get('role') != 'admin': return redirect(url_for('login'))
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT o.id, u.full_name, o.product_name, o.price, o.order_date 
        FROM orders o JOIN users u ON o.user_id = u.id ORDER BY o.order_date DESC
    """)
    orders = cur.fetchall()

    cur.execute("""
        SELECT fc.id, u.full_name, fc.crop_name, fc.status, fc.sown_date 
        FROM farmer_crops fc JOIN users u ON fc.user_id = u.id ORDER BY fc.sown_date DESC
    """)
    crops = cur.fetchall()

    cur.close()
    conn.close()
    return render_template('admin/farmer_activity.html', orders=orders, crops=crops)


# ==========================================
# 6. FARMER DASHBOARD & FEATURES
# ==========================================
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

@app.route('/analytics')
def analytics():
    if 'user_id' not in session: return redirect(url_for('login'))
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # 1. Fetch real historical prices from PostgreSQL
    cur.execute("""
        SELECT c.name, mp.price_per_quintal, TO_CHAR(mp.date, 'Mon') as month
        FROM market_prices mp
        JOIN crops c ON mp.crop_id = c.id
        WHERE c.name IN ('Wheat', 'Rice', 'Cotton')
        ORDER BY mp.date ASC
        LIMIT 50
    """)
    real_data = cur.fetchall()
    cur.close()
    conn.close()

    # 2. Process the data into lists for Chart.js
    months_set = []
    wheat_prices = []
    rice_prices = []
    cotton_prices = []

    for row in real_data:
        crop_name, price, month = row
        if month not in months_set:
            months_set.append(month)
            
        # FIX: Convert the Decimal price to a standard float!
        safe_price = float(price)
            
        if crop_name.lower() == 'wheat': wheat_prices.append(safe_price)
        elif crop_name.lower() == 'rice': rice_prices.append(safe_price)
        elif crop_name.lower() == 'cotton': cotton_prices.append(safe_price)

    # 3. Fallback to dummy data if database is empty (to prevent broken charts during demo)
    if not months_set:
        months_set = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
        wheat_prices = [2100, 2150, 2200, 2180, 2250, 2300]
        rice_prices = [1900, 1850, 1880, 1920, 1950, 1980]
        cotton_prices = [5500, 5600, 5400, 5700, 5900, 6100]

    return render_template('farmer/analytics.html',
                           months=json.dumps(months_set),
                           wheat=json.dumps(wheat_prices),
                           rice=json.dumps(rice_prices),
                           cotton=json.dumps(cotton_prices))

@app.route('/insurance_calculator')
def insurance_calculator():
    if 'user_id' not in session: return redirect(url_for('login'))
    return render_template('farmer/insurance.html')

@app.route('/calculator')
def calculator():
    return render_template('home/calculator.html')

# --- MY CROPS ---
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

# --- CROP GROWING GUIDES ---
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


# ==========================================
# 7. AI MACHINE LEARNING ROUTES
# ==========================================
@app.route('/recommend', methods=['GET', 'POST'])
def recommend():
    if 'user_id' not in session: return redirect(url_for('login'))
    
    prediction = None
    if request.method == 'POST':
        if crop_model:
            try:
                # Grab all 7 inputs from the form (including rainfall)
                N = float(request.form['N'])
                P = float(request.form['P'])
                K = float(request.form['K'])
                temperature = float(request.form['temperature'])
                humidity = float(request.form['humidity'])
                ph = float(request.form['ph'])
                rainfall = float(request.form.get('rainfall', 100)) 
                
                # Format as 2D array for the scikit-learn model
                features = np.array([[N, P, K, temperature, humidity, ph, rainfall]])
                
                # Make Prediction
                prediction = crop_model.predict(features)[0]
            except Exception as e:
                flash(f"Error in prediction logic: {e}", "error")
        else:
            flash("AI Model is currently offline. Please contact Admin.", "error")
            
    return render_template('farmer/recommend.html', prediction=prediction)


# 🌿 DEEP LEARNING COMPUTER VISION ROUTE
@app.route('/plant_doctor', methods=['GET', 'POST'])
def plant_doctor():
    if 'user_id' not in session: return redirect(url_for('login'))
    
    prediction = None
    image_url = None

    if request.method == 'POST':
        if 'leaf_image' not in request.files: return redirect(request.url)
        file = request.files['leaf_image']
        
        if file.filename == '': 
            flash("No file selected", "error")
            return redirect(request.url)

        if file and plant_model:
            try:
                # 1. Save Image properly for static routing
                filename = secure_filename(file.filename)
                save_path = os.path.join('static', 'images', 'leaves', filename)
                file.save(save_path)
                
                # This matches HTML: url_for('static', filename=image_url)
                image_url = "images/leaves/" + filename 
                
                # 2. Preprocess for CNN (Resize to 128x128 and normalize)
                img = load_img(save_path, target_size=(128, 128))
                img_array = img_to_array(img)
                img_array = np.expand_dims(img_array, axis=0) / 255.0
                
                # 3. Predict using TensorFlow
                predictions = plant_model.predict(img_array)
                class_idx = np.argmax(predictions[0])
                confidence = float(np.max(predictions[0])) * 100
                formatted_confidence = f"{confidence:.2f}"
                
                # 4. Format for your beautiful UI
                result_data = DISEASE_INFO.get(class_idx, DISEASE_INFO[0])
                prediction = {
                    "name": result_data["name"],
                    "status": result_data["status"],
                    "cure": result_data["cure"],
                    "confidence": f"{formatted_confidence}%"
}
                
            except Exception as e:
                flash(f"Error processing image: {e}", "error")
        elif not plant_model:
            flash("AI Model is offline. Please contact the administrator.", "error")

    return render_template('farmer/plant_doctor.html', prediction=prediction, image_url=image_url)


# ==========================================
# 8. SHOP, CART & E-COMMERCE ROUTES
# ==========================================
@app.route('/shop')
def shop():
    if 'user_id' not in session: return redirect(url_for('login'))
    products = Product.query.order_by(Product.id.desc()).all()
    return render_template('farmer/shop.html', products=products)

@app.route('/manage_shop', methods=['GET', 'POST'])
def manage_shop():
    if session.get('role') != 'admin': return redirect(url_for('login'))
    if request.method == 'POST':
        return add_product_orm() 
    products = Product.query.order_by(Product.id.desc()).all()
    return render_template('admin/manage_shop.html', products=products)

@app.route('/add_product', methods=['GET', 'POST'])
def add_product_orm(): 
    if session.get('role') != 'admin': return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name']
        category = request.form['category']
        price = float(request.form['price'])
        stock = int(request.form.get('stock', 100)) 
        
        file = request.files['image']
        filename = 'default_product.png'
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        new_product = Product(name=name, category=category, price=price, stock=stock, image_url=filename)
        db.session.add(new_product)
        db.session.commit()
        flash("Product Added to Shop!", "success")
        return redirect(url_for('manage_shop'))

    return render_template('admin/add_product.html')

@app.route('/delete_product/<int:id>')
def delete_product_orm(id):
    if session.get('role') != 'admin': return redirect(url_for('login'))
    product = Product.query.get(id)
    if product:
        db.session.delete(product)
        db.session.commit()
        flash("Product Deleted!", "danger")
    return redirect(url_for('manage_shop'))

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    if 'user_id' not in session: 
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    
    user_id = session['user_id']
    quantity = int(request.form.get('quantity', 1))

    conn = get_db_connection()
    cur = conn.cursor()
    
    # 1. Check if item exists in cart
    cur.execute("SELECT quantity FROM cart WHERE user_id = %s AND product_id = %s", (user_id, product_id))
    existing_item = cur.fetchone()

    # 2. Update or Insert
    if existing_item:
        new_quantity = existing_item[0] + quantity
        cur.execute("UPDATE cart SET quantity = %s WHERE user_id = %s AND product_id = %s", (new_quantity, user_id, product_id))
    else:
        cur.execute("INSERT INTO cart (user_id, product_id, quantity) VALUES (%s, %s, %s)", (user_id, product_id, quantity))

    # 3. Dynamically count the new total items in the cart
    cur.execute("SELECT COUNT(*) FROM cart WHERE user_id = %s", (user_id,))
    total_items = cur.fetchone()[0]

    conn.commit()
    cur.close()
    conn.close()
    
    # 4. Return JSON instead of redirecting the page!
    return jsonify({
        "status": "success",
        "message": f"Successfully added to cart!",
        "cart_count": total_items
    })

@app.route('/cart')
def cart():
    if 'user_id' not in session: return redirect(url_for('login'))
    user_id = session['user_id']
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT c.id, p.name, p.category, p.price, p.image_url, c.quantity, (p.price * c.quantity) as item_total
        FROM cart c JOIN products p ON c.product_id = p.id WHERE c.user_id = %s ORDER BY c.id DESC
    """, (user_id,))
    cart_items = cur.fetchall()
    grand_total = sum(item[6] for item in cart_items) if cart_items else 0
    cur.close()
    conn.close()
    return render_template('farmer/cart.html', cart_items=cart_items, grand_total=grand_total)

@app.route('/remove_from_cart/<int:cart_id>')
def remove_from_cart(cart_id):
    if 'user_id' not in session: return redirect(url_for('login'))
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM cart WHERE id = %s", (cart_id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('cart'))

@app.route('/buy_now/<int:id>')
def buy_now(id):
    if 'user_id' not in session: return redirect(url_for('login'))
    product = Product.query.get(id)
    if product and product.stock > 0:
        product.stock -= 1
        new_order = Order(user_id=session['user_id'], product_name=product.name, price=product.price)
        db.session.add(new_order)
        db.session.commit()
        flash(f"Successfully bought {product.name}!", "success")
    else:
        flash("Out of Stock!", "danger")
    return redirect(url_for('shop'))

@app.route('/checkout')
def checkout():
    if 'user_id' not in session: return redirect(url_for('login'))
    user_id = session['user_id']
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # 1. Fetch what the user is trying to buy
    cur.execute("SELECT product_id, quantity FROM cart WHERE user_id = %s", (user_id,))
    cart_items = cur.fetchall()
    
    # 2. PRO INVENTORY LOGIC: Check & Deduct Stock using SQLAlchemy
    for item in cart_items:
        product_id, quantity = item[0], item[1]
        product = Product.query.get(product_id)
        
        if product and product.stock >= quantity:
            product.stock -= quantity # Deduct the stock!
        elif product:
            flash(f"Not enough stock for {product.name}. Only {product.stock} left!", "error")
            cur.close()
            conn.close()
            return redirect(url_for('cart'))
            
    db.session.commit() # Save the new stock levels to the database
    
    # 3. Create Orders & Clear the Cart
    cur.execute("""
        INSERT INTO orders (user_id, product_name, price)
        SELECT c.user_id, p.name, (p.price * c.quantity)
        FROM cart c JOIN products p ON c.product_id = p.id WHERE c.user_id = %s
    """, (user_id,))
    cur.execute("DELETE FROM cart WHERE user_id = %s", (user_id,))
    
    conn.commit()
    cur.close()
    conn.close()
    
    return render_template('farmer/order_success.html')

# ==========================================
# 9. PUBLIC INFORMATION ROUTES
# ==========================================
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
    
    # Optional: Connect this back to the OpenWeather API like in the /home route
    weather_data = {'temp': 28, 'humidity': 60, 'wind': 10, 'desc': 'Sunny ☀️'}
    return render_template('home/weather.html', weather=weather_data, city=city)

@app.route('/news_schemes')
def news_schemes():
    api_key = "cef4263381c9470e8ec5a5848e88e2ff"
    url = f"https://newsapi.org/v2/everything?q=agriculture+india&sortBy=publishedAt&language=en&apiKey={api_key}"
    updates = []
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            updates = resp.json().get('articles', [])[:6]
    except Exception as e:
        print("News API Error:", e)

    core_schemes = [
        {"title": "Pradhan Mantri Fasal Bima Yojana", "description": "Crop insurance scheme to provide financial support.", "link": "https://pmfby.gov.in/", "icon": "🛡️"},
        {"title": "PM-KISAN Samman Nidhi", "description": "Financial benefit of ₹6,000 per year for farmers.", "link": "https://pmkisan.gov.in/", "icon": "💰"},
        {"title": "Kisan Credit Card (KCC)", "description": "Access to affordable credit for farmers.", "link": "https://www.myscheme.gov.in/schemes/kcc", "icon": "💳"}
    ]

    if 'user_id' in session:
        return render_template('farmer/news_schemes.html', updates=updates, schemes=core_schemes)
    else:
        return render_template('home/news.html', updates=updates, schemes=core_schemes)

@app.route('/admin_inventory')
def admin_inventory():
    if session.get('role') != 'admin': return redirect(url_for('login'))
    
    # Fetch all products, ordering by lowest stock first so Admin sees urgent items
    products = Product.query.order_by(Product.stock.asc()).all()
    return render_template('admin/inventory.html', products=products)

@app.route('/restock/<int:product_id>', methods=['POST'])
def restock(product_id):
    if session.get('role') != 'admin': return redirect(url_for('login'))
    
    product = Product.query.get(product_id)
    if product:
        added_stock = int(request.form.get('added_stock', 0))
        product.stock += added_stock
        db.session.commit()
        flash(f"Successfully restocked {product.name}!", "success")
        
    return redirect(url_for('admin_inventory'))

# ==========================================
# APPLICATION ENTRY POINT
# ==========================================
if __name__ == '__main__':
    app.run(debug=True)