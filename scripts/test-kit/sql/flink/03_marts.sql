-- Mart Tables (Kafka → PostgreSQL analytics)
-- Each mart reads from staging Kafka topics and writes to PostgreSQL via JDBC.
-- These are separate streaming jobs that run indefinitely.

SET 'execution.runtime-mode' = 'streaming';

-- enriched_orders: join orders with users, sink to PG
CREATE TEMPORARY TABLE enriched_orders (
  `order_id` INT,
  `user_id` INT,
  `username` STRING,
  `email` STRING,
  `user_status` STRING,
  `product_name` STRING,
  `quantity` INT,
  `price` DECIMAL(10, 2),
  `total_amount` DECIMAL(10, 2),
  `order_date` TIMESTAMP(3),
  `order_status` STRING,
  `updated_at` TIMESTAMP(3),
  PRIMARY KEY (order_id) NOT ENFORCED
) WITH (
  'connector' = 'jdbc',
  'url' = 'jdbc:postgresql://postgres:5432/testdb',
  'table-name' = 'analytics.enriched_orders',
  'username' = 'postgres',
  'password' = 'postgres',
  'sink.buffer-flush.max-rows' = '100',
  'sink.buffer-flush.interval' = '1s'
);

INSERT INTO enriched_orders
SELECT
    o.order_id,
    o.user_id,
    u.username,
    u.email,
    u.status AS user_status,
    o.product_name,
    o.quantity,
    o.price,
    o.total_amount,
    o.order_date,
    o.status AS order_status,
    o.order_date AS updated_at
FROM stg_orders o
LEFT JOIN stg_users u
    ON o.user_id = u.user_id;

-- user_activity_summary: users sink to PG
CREATE TEMPORARY TABLE user_activity_summary (
  `user_id` INT,
  `username` STRING,
  `email` STRING,
  `status` STRING,
  `created_at` TIMESTAMP(3),
  `updated_at` TIMESTAMP(3),
  PRIMARY KEY (user_id) NOT ENFORCED
) WITH (
  'connector' = 'jdbc',
  'url' = 'jdbc:postgresql://postgres:5432/testdb',
  'table-name' = 'analytics.user_activity_summary',
  'username' = 'postgres',
  'password' = 'postgres',
  'sink.buffer-flush.max-rows' = '100',
  'sink.buffer-flush.interval' = '1s'
);

INSERT INTO user_activity_summary
SELECT user_id, username, email, status, created_at, updated_at
FROM stg_users;

-- event_counts: events sink to PG
CREATE TEMPORARY TABLE event_counts (
  `event_id` INT,
  `user_id` INT,
  `event_type` STRING,
  `event_data` STRING,
  `event_timestamp` TIMESTAMP(3),
  PRIMARY KEY (event_id) NOT ENFORCED
) WITH (
  'connector' = 'jdbc',
  'url' = 'jdbc:postgresql://postgres:5432/testdb',
  'table-name' = 'analytics.event_counts',
  'username' = 'postgres',
  'password' = 'postgres',
  'sink.buffer-flush.max-rows' = '100',
  'sink.buffer-flush.interval' = '1s'
);

INSERT INTO event_counts
SELECT event_id, user_id, event_type, event_data, event_timestamp
FROM stg_events;
