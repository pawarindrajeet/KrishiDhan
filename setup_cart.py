import psycopg2
from config import Config

conn = psycopg2.connect(
    host=Config.DB_HOST,
    database=Config.DB_NAME,
    user=Config.DB_USER,
    password=Config.DB_PASS
)
cur = conn.cursor()

# Create Cart Table
cur.execute("""
    CREATE TABLE IF NOT EXISTS cart (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER DEFAULT 1,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (product_id) REFERENCES products (id)
    );
""")

conn.commit()
cur.close()
conn.close()
print("✅ Cart table created successfully!")