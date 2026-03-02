-- Create the Hive Metastore database and user.
-- This runs automatically on first PostgreSQL startup via docker-entrypoint-initdb.d.

-- Create the hive user for Hive Metastore
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'hive') THEN
        CREATE ROLE hive WITH LOGIN PASSWORD 'hive';
    END IF;
END
$$;

-- Create the metastore database
SELECT 'CREATE DATABASE metastore_db OWNER hive'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'metastore_db')\gexec

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE metastore_db TO hive;
