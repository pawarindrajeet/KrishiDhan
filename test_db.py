import psycopg2
from config import Config

try:
    print("Attempting to connect to the database...")
    
    # Try connecting using details from config.py
    conn = psycopg2.connect(
        host=Config.DB_HOST,
        database=Config.DB_NAME,
        user=Config.DB_USER,
        password=Config.DB_PASS
    )
    
    print("✅ SUCCESS! Python is connected to PostgreSQL.")
    conn.close()

except Exception as e:
    print("❌ ERROR: Could not connect.")
    print("Error details:", e)