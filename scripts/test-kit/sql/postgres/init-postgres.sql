-- PostgreSQL initialization script for Flink testing
-- Creates test tables with sample data

-- Create schema
CREATE SCHEMA IF NOT EXISTS flink_test;

-- Create users table
CREATE TABLE flink_test.users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active'
);

-- Create orders table
CREATE TABLE flink_test.orders (
    order_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES flink_test.users(user_id),
    product_name VARCHAR(100) NOT NULL,
    quantity INTEGER NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    total_amount DECIMAL(10, 2) GENERATED ALWAYS AS (quantity * price) STORED,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'pending'
);

-- Create events table for streaming
CREATE TABLE flink_test.events (
    event_id SERIAL PRIMARY KEY,
    user_id INTEGER,
    event_type VARCHAR(50) NOT NULL,
    event_data JSONB,
    event_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample users
INSERT INTO flink_test.users (username, email, status) VALUES
    ('alice', 'alice@example.com', 'active'),
    ('bob', 'bob@example.com', 'active'),
    ('charlie', 'charlie@example.com', 'active'),
    ('diana', 'diana@example.com', 'inactive'),
    ('eve', 'eve@example.com', 'active');

-- Insert sample orders
INSERT INTO flink_test.orders (user_id, product_name, quantity, price, status) VALUES
    (1, 'Laptop', 1, 1200.00, 'completed'),
    (1, 'Mouse', 2, 25.00, 'completed'),
    (2, 'Keyboard', 1, 80.00, 'pending'),
    (3, 'Monitor', 2, 350.00, 'completed'),
    (3, 'USB Cable', 5, 10.00, 'completed'),
    (2, 'Headphones', 1, 150.00, 'shipped'),
    (5, 'Webcam', 1, 75.00, 'pending');

-- Insert sample events
INSERT INTO flink_test.events (user_id, event_type, event_data) VALUES
    (1, 'login', '{"ip": "192.168.1.1", "device": "chrome"}'),
    (1, 'page_view', '{"page": "/products", "duration": 45}'),
    (2, 'login', '{"ip": "192.168.1.2", "device": "firefox"}'),
    (3, 'purchase', '{"product_id": 123, "amount": 350.00}'),
    (1, 'logout', '{"duration": 3600}');

-- Create function to generate continuous events (for testing)
CREATE OR REPLACE FUNCTION flink_test.generate_event()
RETURNS TRIGGER AS $$
BEGIN
    -- This will be called by an external process
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions
GRANT ALL PRIVILEGES ON SCHEMA flink_test TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA flink_test TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA flink_test TO postgres;

-- Create publication for logical replication (CDC)
CREATE PUBLICATION flink_cdc_publication FOR ALL TABLES;

-- Show configuration
SELECT name, setting FROM pg_settings
WHERE name IN ('wal_level', 'max_replication_slots', 'max_wal_senders');

-- Show created objects
\dt flink_test.*;
