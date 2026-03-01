-- =============================================================================
-- Job 1: MongoDB CDC → Kafka (continuous streaming)
-- Reads change streams from MongoDB and writes to Kafka topics.
-- Self-contained: all table definitions + INSERT statements.
-- =============================================================================

SET 'execution.runtime-mode' = 'streaming';
SET 'execution.checkpointing.interval' = '10s';

-- MongoDB CDC source tables
CREATE TABLE mongo_customers (
    _id            STRING,
    customer_id    STRING,
    name           STRING,
    email          STRING,
    city           STRING,
    created_at     TIMESTAMP(3),
    PRIMARY KEY (_id) NOT ENFORCED
) WITH (
    'connector' = 'mongodb-cdc',
    'hosts' = 'mongodb:27017',
    'database' = 'ecommerce',
    'collection' = 'customers'
);

CREATE TABLE mongo_products (
    _id            STRING,
    product_id     STRING,
    name           STRING,
    category       STRING,
    price          DECIMAL(10, 2),
    stock          INT,
    PRIMARY KEY (_id) NOT ENFORCED
) WITH (
    'connector' = 'mongodb-cdc',
    'hosts' = 'mongodb:27017',
    'database' = 'ecommerce',
    'collection' = 'products'
);

CREATE TABLE mongo_orders (
    _id            STRING,
    order_id       STRING,
    customer_id    STRING,
    product_id     STRING,
    quantity        INT,
    total          DECIMAL(10, 2),
    status         STRING,
    created_at     TIMESTAMP(3),
    updated_at     TIMESTAMP(3),
    PRIMARY KEY (_id) NOT ENFORCED
) WITH (
    'connector' = 'mongodb-cdc',
    'hosts' = 'mongodb:27017',
    'database' = 'ecommerce',
    'collection' = 'orders'
);

-- Kafka sink tables (upsert-kafka for CDC update/delete semantics)
CREATE TABLE kafka_customers (
    customer_id    STRING,
    name           STRING,
    email          STRING,
    city           STRING,
    created_at     TIMESTAMP(3),
    PRIMARY KEY (customer_id) NOT ENFORCED
) WITH (
    'connector' = 'upsert-kafka',
    'topic' = 'demo-customers',
    'properties.bootstrap.servers' = 'kafka:29093',
    'key.format' = 'json',
    'value.format' = 'json'
);

CREATE TABLE kafka_products (
    product_id     STRING,
    name           STRING,
    category       STRING,
    price          DECIMAL(10, 2),
    stock          INT,
    PRIMARY KEY (product_id) NOT ENFORCED
) WITH (
    'connector' = 'upsert-kafka',
    'topic' = 'demo-products',
    'properties.bootstrap.servers' = 'kafka:29093',
    'key.format' = 'json',
    'value.format' = 'json'
);

CREATE TABLE kafka_orders (
    order_id       STRING,
    customer_id    STRING,
    product_id     STRING,
    quantity        INT,
    total          DECIMAL(10, 2),
    status         STRING,
    created_at     TIMESTAMP(3),
    updated_at     TIMESTAMP(3),
    PRIMARY KEY (order_id) NOT ENFORCED
) WITH (
    'connector' = 'upsert-kafka',
    'topic' = 'demo-orders',
    'properties.bootstrap.servers' = 'kafka:29093',
    'key.format' = 'json',
    'value.format' = 'json'
);

-- Start continuous streaming: MongoDB CDC → Kafka
EXECUTE STATEMENT SET
BEGIN
    INSERT INTO kafka_customers
    SELECT customer_id, name, email, city, created_at
    FROM mongo_customers;

    INSERT INTO kafka_products
    SELECT product_id, name, category, price, stock
    FROM mongo_products;

    INSERT INTO kafka_orders
    SELECT order_id, customer_id, product_id, quantity, total, status, created_at, updated_at
    FROM mongo_orders;
END;
