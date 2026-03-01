-- =============================================================================
-- Full pipeline: MongoDB CDC → Kafka → PostgreSQL
-- Executed as a single sql-client session so all tables are visible.
-- =============================================================================

SET 'execution.runtime-mode' = 'streaming';
SET 'execution.checkpointing.interval' = '10s';

-- =============================================================================
-- PART 1: MongoDB CDC source tables
-- =============================================================================

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

-- =============================================================================
-- PART 2: Kafka staging tables (upsert-kafka for CDC semantics)
-- =============================================================================

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

-- =============================================================================
-- PART 3: PostgreSQL JDBC sink tables
-- =============================================================================

CREATE TABLE pg_customers (
    customer_id    STRING,
    name           STRING,
    email          STRING,
    city           STRING,
    created_at     TIMESTAMP(3),
    PRIMARY KEY (customer_id) NOT ENFORCED
) WITH (
    'connector' = 'jdbc',
    'url' = 'jdbc:postgresql://postgres:5432/demodb',
    'table-name' = 'demo.customers',
    'username' = 'postgres',
    'password' = 'postgres',
    'driver' = 'org.postgresql.Driver',
    'sink.buffer-flush.max-rows' = '100',
    'sink.buffer-flush.interval' = '1s'
);

CREATE TABLE pg_products (
    product_id     STRING,
    name           STRING,
    category       STRING,
    price          DECIMAL(10, 2),
    stock          INT,
    PRIMARY KEY (product_id) NOT ENFORCED
) WITH (
    'connector' = 'jdbc',
    'url' = 'jdbc:postgresql://postgres:5432/demodb',
    'table-name' = 'demo.products',
    'username' = 'postgres',
    'password' = 'postgres',
    'driver' = 'org.postgresql.Driver',
    'sink.buffer-flush.max-rows' = '100',
    'sink.buffer-flush.interval' = '1s'
);

CREATE TABLE pg_orders (
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
    'connector' = 'jdbc',
    'url' = 'jdbc:postgresql://postgres:5432/demodb',
    'table-name' = 'demo.orders',
    'username' = 'postgres',
    'password' = 'postgres',
    'driver' = 'org.postgresql.Driver',
    'sink.buffer-flush.max-rows' = '100',
    'sink.buffer-flush.interval' = '1s'
);

-- =============================================================================
-- PART 4: Start all streaming jobs
-- MongoDB CDC → Kafka, then Kafka → PostgreSQL
-- =============================================================================

EXECUTE STATEMENT SET
BEGIN
    -- MongoDB CDC → Kafka
    INSERT INTO kafka_customers
    SELECT customer_id, name, email, city, created_at
    FROM mongo_customers;

    INSERT INTO kafka_products
    SELECT product_id, name, category, price, stock
    FROM mongo_products;

    INSERT INTO kafka_orders
    SELECT order_id, customer_id, product_id, quantity, total, status, created_at, updated_at
    FROM mongo_orders;

    -- Kafka → PostgreSQL
    INSERT INTO pg_customers
    SELECT customer_id, name, email, city, created_at
    FROM kafka_customers;

    INSERT INTO pg_products
    SELECT product_id, name, category, price, stock
    FROM kafka_products;

    INSERT INTO pg_orders
    SELECT order_id, customer_id, product_id, quantity, total, status, created_at, updated_at
    FROM kafka_orders;
END;
