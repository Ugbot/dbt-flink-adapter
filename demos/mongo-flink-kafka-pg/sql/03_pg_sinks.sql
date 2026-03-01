-- Kafka source → PostgreSQL JDBC sink tables and streaming jobs.
-- Reads from Kafka topics written by the MongoDB CDC pipeline and lands into PG.

SET 'execution.runtime-mode' = 'streaming';

-- Kafka source tables (reading from topics populated by 02_kafka_sinks.sql)
CREATE TABLE IF NOT EXISTS kafka_src_customers (
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
    'properties.group.id' = 'flink-pg-customers',
    'key.format' = 'json',
    'value.format' = 'json'
);

CREATE TABLE IF NOT EXISTS kafka_src_products (
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
    'properties.group.id' = 'flink-pg-products',
    'key.format' = 'json',
    'value.format' = 'json'
);

CREATE TABLE IF NOT EXISTS kafka_src_orders (
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
    'properties.group.id' = 'flink-pg-orders',
    'key.format' = 'json',
    'value.format' = 'json'
);

-- PostgreSQL JDBC sink tables
CREATE TABLE IF NOT EXISTS pg_customers (
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

CREATE TABLE IF NOT EXISTS pg_products (
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

CREATE TABLE IF NOT EXISTS pg_orders (
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

-- Start streaming jobs: Kafka → PostgreSQL
EXECUTE STATEMENT SET
BEGIN
    INSERT INTO pg_customers
    SELECT customer_id, name, email, city, created_at
    FROM kafka_src_customers;

    INSERT INTO pg_products
    SELECT product_id, name, category, price, stock
    FROM kafka_src_products;

    INSERT INTO pg_orders
    SELECT order_id, customer_id, product_id, quantity, total, status, created_at, updated_at
    FROM kafka_src_orders;
END;
