import psycopg2
from config import Config

# Connect to Database
conn = psycopg2.connect(
    host=Config.DB_HOST,
    database=Config.DB_NAME,
    user=Config.DB_USER,
    password=Config.DB_PASS
)
cur = conn.cursor()

# Create the 'farmer_crops' table
cur.execute("""
    CREATE TABLE IF NOT EXISTS farmer_crops (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id),
        crop_name VARCHAR(100),
        sown_date DATE,
        status VARCHAR(50),
        next_action TEXT
    );
""")

conn.commit()
cur.close()
conn.close()

print("✅ Success! Table 'farmer_crops' created.")