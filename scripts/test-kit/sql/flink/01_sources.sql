-- CDC Source Tables
-- These create TEMPORARY tables that read from PostgreSQL WAL via CDC connectors.
-- Each source becomes a streaming changelog that Flink can process.

SET 'execution.runtime-mode' = 'streaming';

-- Users CDC source
CREATE TEMPORARY TABLE postgres_cdc_users (
  `user_id` INT,
  `username` STRING,
  `email` STRING,
  `created_at` TIMESTAMP(3),
  `updated_at` TIMESTAMP(3),
  `status` STRING,
  PRIMARY KEY (user_id) NOT ENFORCED
) WITH (
  'connector' = 'postgres-cdc',
  'hostname' = 'postgres',
  'port' = '5432',
  'username' = 'postgres',
  'password' = 'postgres',
  'database-name' = 'testdb',
  'schema-name' = 'flink_test',
  'table-name' = 'users',
  'slot.name' = 'flink_e2e_users_slot',
  'decoding.plugin.name' = 'pgoutput'
);

-- Orders CDC source
CREATE TEMPORARY TABLE postgres_cdc_orders (
  `order_id` INT,
  `user_id` INT,
  `product_name` STRING,
  `quantity` INT,
  `price` DECIMAL(10, 2),
  `order_date` TIMESTAMP(3),
  `status` STRING,
  PRIMARY KEY (order_id) NOT ENFORCED
) WITH (
  'connector' = 'postgres-cdc',
  'hostname' = 'postgres',
  'port' = '5432',
  'username' = 'postgres',
  'password' = 'postgres',
  'database-name' = 'testdb',
  'schema-name' = 'flink_test',
  'table-name' = 'orders',
  'slot.name' = 'flink_e2e_orders_slot',
  'decoding.plugin.name' = 'pgoutput'
);

-- Events CDC source
CREATE TEMPORARY TABLE postgres_cdc_events (
  `event_id` INT,
  `user_id` INT,
  `event_type` STRING,
  `event_data` STRING,
  `event_timestamp` TIMESTAMP(3),
  PRIMARY KEY (event_id) NOT ENFORCED
) WITH (
  'connector' = 'postgres-cdc',
  'hostname' = 'postgres',
  'port' = '5432',
  'username' = 'postgres',
  'password' = 'postgres',
  'database-name' = 'testdb',
  'schema-name' = 'flink_test',
  'table-name' = 'events',
  'slot.name' = 'flink_e2e_events_slot',
  'decoding.plugin.name' = 'pgoutput'
);
