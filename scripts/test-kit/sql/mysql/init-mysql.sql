-- MySQL initialization script for Flink testing
-- Creates test tables with sample data

-- Create database and switch to it
CREATE DATABASE IF NOT EXISTS flink_test;
USE flink_test;

-- Grant CDC replication privileges to the flink user.
-- The MYSQL_USER env var in docker-compose.yml creates 'flink'@'%' with access to testdb,
-- but CDC requires global REPLICATION SLAVE + REPLICATION CLIENT, plus SELECT on flink_test.
GRANT REPLICATION SLAVE, REPLICATION CLIENT ON *.* TO 'flink'@'%';
GRANT ALL PRIVILEGES ON flink_test.* TO 'flink'@'%';
FLUSH PRIVILEGES;

-- Create customers table
CREATE TABLE customers (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    phone VARCHAR(20),
    address VARCHAR(255),
    city VARCHAR(50),
    country VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Create products table
CREATE TABLE products (
    product_id INT AUTO_INCREMENT PRIMARY KEY,
    product_name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    stock_quantity INT NOT NULL DEFAULT 0,
    supplier_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'available'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Create transactions table for streaming
CREATE TABLE transactions (
    transaction_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    total_amount DECIMAL(10, 2) GENERATED ALWAYS AS (quantity * unit_price) STORED,
    payment_method VARCHAR(50),
    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'pending',
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Create inventory_events table for CDC testing
CREATE TABLE inventory_events (
    event_id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    quantity_change INT NOT NULL,
    previous_stock INT,
    new_stock INT,
    event_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    FOREIGN KEY (product_id) REFERENCES products(product_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Insert sample customers
INSERT INTO customers (customer_name, email, phone, address, city, country, status) VALUES
    ('John Smith', 'john.smith@example.com', '+1-555-0101', '123 Main St', 'New York', 'USA', 'active'),
    ('Maria Garcia', 'maria.garcia@example.com', '+1-555-0102', '456 Oak Ave', 'Los Angeles', 'USA', 'active'),
    ('Wei Chen', 'wei.chen@example.com', '+86-555-0103', '789 Pine Rd', 'Beijing', 'China', 'active'),
    ('Emma Wilson', 'emma.wilson@example.com', '+44-555-0104', '321 Elm St', 'London', 'UK', 'active'),
    ('Ahmed Hassan', 'ahmed.hassan@example.com', '+971-555-0105', '654 Cedar Ln', 'Dubai', 'UAE', 'inactive');

-- Insert sample products
INSERT INTO products (product_name, category, price, stock_quantity, supplier_id, status) VALUES
    ('MacBook Pro 16"', 'Electronics', 2499.99, 50, 1, 'available'),
    ('iPhone 15 Pro', 'Electronics', 1199.99, 100, 1, 'available'),
    ('Sony WH-1000XM5', 'Audio', 399.99, 75, 2, 'available'),
    ('Samsung 4K Monitor', 'Electronics', 549.99, 30, 3, 'available'),
    ('Logitech MX Master 3', 'Accessories', 99.99, 150, 2, 'available'),
    ('Apple Magic Keyboard', 'Accessories', 149.99, 80, 1, 'available'),
    ('Dell XPS 15', 'Electronics', 1899.99, 25, 3, 'available');

-- Insert sample transactions
INSERT INTO transactions (customer_id, product_id, quantity, unit_price, payment_method, status) VALUES
    (1, 1, 1, 2499.99, 'credit_card', 'completed'),
    (1, 5, 2, 99.99, 'credit_card', 'completed'),
    (2, 2, 1, 1199.99, 'paypal', 'completed'),
    (3, 4, 2, 549.99, 'credit_card', 'pending'),
    (3, 3, 1, 399.99, 'credit_card', 'completed'),
    (4, 6, 1, 149.99, 'debit_card', 'shipped'),
    (2, 7, 1, 1899.99, 'credit_card', 'processing');

-- Insert sample inventory events
INSERT INTO inventory_events (product_id, event_type, quantity_change, previous_stock, new_stock, notes) VALUES
    (1, 'RESTOCK', 50, 0, 50, 'Initial inventory'),
    (2, 'RESTOCK', 100, 0, 100, 'Initial inventory'),
    (1, 'SALE', -1, 50, 49, 'Sold to customer #1'),
    (5, 'SALE', -2, 150, 148, 'Sold to customer #1'),
    (2, 'SALE', -1, 100, 99, 'Sold to customer #2');

-- Create indexes for better query performance
CREATE INDEX idx_customers_status ON customers(status);
CREATE INDEX idx_customers_city ON customers(city);
CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_products_status ON products(status);
CREATE INDEX idx_transactions_customer ON transactions(customer_id);
CREATE INDEX idx_transactions_date ON transactions(transaction_date);
CREATE INDEX idx_transactions_status ON transactions(status);
CREATE INDEX idx_inventory_product ON inventory_events(product_id);
CREATE INDEX idx_inventory_timestamp ON inventory_events(event_timestamp);

-- Create view for transaction summaries
CREATE VIEW transaction_summary AS
SELECT
    t.transaction_id,
    c.customer_name,
    c.email,
    p.product_name,
    p.category,
    t.quantity,
    t.unit_price,
    t.total_amount,
    t.payment_method,
    t.transaction_date,
    t.status
FROM transactions t
JOIN customers c ON t.customer_id = c.customer_id
JOIN products p ON t.product_id = p.product_id;

-- Verify binlog settings for CDC
SELECT @@log_bin as binlog_enabled,
       @@binlog_format as binlog_format,
       @@binlog_row_image as binlog_row_image,
       @@gtid_mode as gtid_mode,
       @@enforce_gtid_consistency as enforce_gtid_consistency;

-- Show created objects
SHOW TABLES;

-- Display table row counts
SELECT 'customers' as table_name, COUNT(*) as row_count FROM customers
UNION ALL
SELECT 'products', COUNT(*) FROM products
UNION ALL
SELECT 'transactions', COUNT(*) FROM transactions
UNION ALL
SELECT 'inventory_events', COUNT(*) FROM inventory_events;
