{{
  config(
    materialized='table',
    catalog_managed=true,
    connector_properties=lakehouse_table_properties(primary_key=false)
  )
}}

{#
  Bronze Layer: Raw Users
  =======================
  User dimension data ingested into the lakehouse. In production, this
  would come from a CDC source (PostgreSQL, MySQL) or a user service API.

  Schema:
    - user_id: Unique user identifier
    - username: Display name
    - email: Email address
    - city: User's city
    - signup_date: When the user signed up
    - is_premium: Whether the user has a premium subscription
#}

SELECT
  user_id,
  username,
  CONCAT(LOWER(username), '@example.com') AS email,
  city,
  TIMESTAMP '2023-01-01 00:00:00' AS signup_date,
  CASE WHEN MOD(user_id, 3) = 0 THEN TRUE ELSE FALSE END AS is_premium
FROM (
  VALUES
    (101, 'alice',   'New York'),
    (102, 'bob',     'San Francisco'),
    (103, 'charlie', 'Chicago'),
    (104, 'diana',   'Austin'),
    (105, 'eve',     'Seattle'),
    (106, 'frank',   'Boston'),
    (107, 'grace',   'Denver'),
    (108, 'henry',   'Portland'),
    (109, 'iris',    'Miami'),
    (110, 'jack',    'Dallas'),
    (111, 'kate',    'Atlanta'),
    (112, 'leo',     'Phoenix'),
    (113, 'mia',     'Detroit'),
    (114, 'noah',    'Minneapolis'),
    (115, 'olivia',  'Nashville'),
    (116, 'peter',   'Charlotte'),
    (117, 'quinn',   'Tampa'),
    (118, 'rachel',  'Orlando'),
    (119, 'sam',     'Las Vegas'),
    (120, 'tara',    'Salt Lake City')
) AS t(user_id, username, city)
