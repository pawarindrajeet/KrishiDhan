-- 1. Table to store Users (Farmers and Admin)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE,
    mobile VARCHAR(15) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(10) CHECK (role IN ('admin', 'farmer')) NOT NULL,
    state VARCHAR(50),
    district VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Table to store Crop Information
CREATE TABLE crops (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL, -- e.g., Fruits, Vegetables
    image_url VARCHAR(200),
    description TEXT,
    soil_type VARCHAR(100),
    season VARCHAR(50),
    growth_stages TEXT, -- Can store JSON or text description
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Table to store Market Prices (Data Science will use this later!)
CREATE TABLE market_prices (
    id SERIAL PRIMARY KEY,
    crop_id INTEGER REFERENCES crops(id),
    state VARCHAR(50),
    district VARCHAR(50),
    price_per_quintal DECIMAL(10, 2),
    date DATE DEFAULT CURRENT_DATE
);