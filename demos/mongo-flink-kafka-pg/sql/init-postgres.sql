-- PostgreSQL target schema for the MongoDB → Flink → Kafka → PG pipeline
-- These tables receive data from Flink JDBC sink connectors.

CREATE SCHEMA IF NOT EXISTS demo;

-- Customers dimension table
CREATE TABLE IF NOT EXISTS demo.customers (
    customer_id    VARCHAR(64) PRIMARY KEY,
    name           VARCHAR(255) NOT NULL,
    email          VARCHAR(255),
    city           VARCHAR(128),
    created_at     TIMESTAMP(3)
);

-- Products dimension table
CREATE TABLE IF NOT EXISTS demo.products (
    product_id     VARCHAR(64) PRIMARY KEY,
    name           VARCHAR(255) NOT NULL,
    category       VARCHAR(128),
    price          DECIMAL(10, 2),
    stock          INTEGER
);

-- Orders fact table
CREATE TABLE IF NOT EXISTS demo.orders (
    order_id       VARCHAR(64) PRIMARY KEY,
    customer_id    VARCHAR(64),
    product_id     VARCHAR(64),
    quantity       INTEGER,
    total          DECIMAL(10, 2),
    status         VARCHAR(32),
    created_at     TIMESTAMP(3),
    updated_at     TIMESTAMP(3)
);

-- Indexes for Grafana dashboard queries
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON demo.orders (created_at);
CREATE INDEX IF NOT EXISTS idx_orders_status ON demo.orders (status);
CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON demo.orders (customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_product_id ON demo.orders (product_id);

-- Verify
SELECT 'PostgreSQL demo schema initialized' AS status;
