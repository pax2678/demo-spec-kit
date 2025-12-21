-- Initialize TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Create database user if not exists
DO $$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'dashboard_user') THEN
      CREATE USER dashboard_user WITH PASSWORD 'dashboard_password';
   END IF;
END
$$;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE dashboard_db TO dashboard_user;
GRANT ALL ON SCHEMA public TO dashboard_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO dashboard_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO dashboard_user;