import os

class Config:
    # Database configuration
    DB_HOST = "localhost"
    DB_NAME = "krishidhan_db"
    DB_USER = "postgres"  # This is usually 'postgres' by default
    DB_PASS = "Admin"  # <--- PUT YOUR PGADMIN PASSWORD HERE
    
    # Secret key for sessions (login security)
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard_to_guess_string'