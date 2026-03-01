-- MongoDB CDC source tables
-- These read change streams from MongoDB replica set collections.

SET 'execution.runtime-mode' = 'streaming';
SET 'sql-client.execution.result-mode' = 'changelog';

CREATE TABLE IF NOT EXISTS mongo_customers (
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

CREATE TABLE IF NOT EXISTS mongo_products (
    _id            STRING,
    customer_id    STRING,
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

CREATE TABLE IF NOT EXISTS mongo_orders (
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
