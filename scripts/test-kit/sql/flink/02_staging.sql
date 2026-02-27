-- Staging Tables (CDC → Kafka)
-- Each staging table is an upsert-kafka sink that receives CDC changes.
-- These are separate streaming jobs that run indefinitely.

SET 'execution.runtime-mode' = 'streaming';

-- stg_users: CDC → Kafka
CREATE TEMPORARY TABLE stg_users (
  `user_id` INT,
  `username` STRING,
  `email` STRING,
  `created_at` TIMESTAMP(3),
  `updated_at` TIMESTAMP(3),
  `status` STRING,
  PRIMARY KEY (user_id) NOT ENFORCED
) WITH (
  'connector' = 'upsert-kafka',
  'topic' = 'e2e-cdc-users',
  'properties.bootstrap.servers' = 'kafka:29092',
  'key.format' = 'json',
  'value.format' = 'json'
);

INSERT INTO stg_users
SELECT user_id, username, email, created_at, updated_at, status
FROM postgres_cdc_users;

-- stg_orders: CDC → Kafka
CREATE TEMPORARY TABLE stg_orders (
  `order_id` INT,
  `user_id` INT,
  `product_name` STRING,
  `quantity` INT,
  `price` DECIMAL(10, 2),
  `total_amount` DECIMAL(10, 2),
  `order_date` TIMESTAMP(3),
  `status` STRING,
  PRIMARY KEY (order_id) NOT ENFORCED
) WITH (
  'connector' = 'upsert-kafka',
  'topic' = 'e2e-cdc-orders',
  'properties.bootstrap.servers' = 'kafka:29092',
  'key.format' = 'json',
  'value.format' = 'json'
);

INSERT INTO stg_orders
SELECT order_id, user_id, product_name, quantity, price,
       quantity * price AS total_amount, order_date, status
FROM postgres_cdc_orders;

-- stg_events: CDC → Kafka
CREATE TEMPORARY TABLE stg_events (
  `event_id` INT,
  `user_id` INT,
  `event_type` STRING,
  `event_data` STRING,
  `event_timestamp` TIMESTAMP(3),
  PRIMARY KEY (event_id) NOT ENFORCED
) WITH (
  'connector' = 'upsert-kafka',
  'topic' = 'e2e-cdc-events',
  'properties.bootstrap.servers' = 'kafka:29092',
  'key.format' = 'json',
  'value.format' = 'json'
);

INSERT INTO stg_events
SELECT event_id, user_id, event_type, event_data, event_timestamp
FROM postgres_cdc_events;
