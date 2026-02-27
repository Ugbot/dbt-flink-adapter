-- PostgreSQL analytics schema initialization
-- Creates sink tables for Flink JDBC connector output.
-- These tables receive enriched/aggregated data from Flink streaming jobs.

CREATE SCHEMA IF NOT EXISTS analytics;

-- Enriched orders: joined orders + user data from Flink streaming pipeline
CREATE TABLE IF NOT EXISTS analytics.enriched_orders (
    order_id INT PRIMARY KEY,
    user_id INT,
    username VARCHAR(100),
    email VARCHAR(200),
    user_status VARCHAR(20),
    product_name VARCHAR(200),
    quantity INT,
    price DECIMAL(10,2),
    total_amount DECIMAL(10,2),
    order_date TIMESTAMP,
    order_status VARCHAR(20),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User activity summary: pass-through of user data for dashboard queries
CREATE TABLE IF NOT EXISTS analytics.user_activity_summary (
    user_id INT PRIMARY KEY,
    username VARCHAR(100),
    email VARCHAR(200),
    status VARCHAR(20),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Event counts: pass-through of event data for dashboard queries
CREATE TABLE IF NOT EXISTS analytics.event_counts (
    event_id INT PRIMARY KEY,
    user_id INT,
    event_type VARCHAR(50),
    event_data TEXT,
    event_timestamp TIMESTAMP
);

-- Grant access
GRANT ALL ON SCHEMA analytics TO postgres;
GRANT ALL ON ALL TABLES IN SCHEMA analytics TO postgres;
