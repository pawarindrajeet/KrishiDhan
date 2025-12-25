import psycopg2
from config import Config

# Connect to your database
conn = psycopg2.connect(
    host=Config.DB_HOST,
    database=Config.DB_NAME,
    user=Config.DB_USER,
    password=Config.DB_PASS
)
cur = conn.cursor()

print("🛠️ Fixing Database...")

# 1. Create ORDERS Table (This is missing!)
cur.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id),
        product_name VARCHAR(100),
        price DECIMAL(10,2),
        order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
""")

# 2. Create PRODUCTS Table (Just in case)
cur.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100),
        category VARCHAR(50),
        price DECIMAL(10,2),
        image_url VARCHAR(200)
    );
""")

conn.commit()
cur.close()
conn.close()
print("✅ Success! 'orders' table created. You can now use Activity Log.")