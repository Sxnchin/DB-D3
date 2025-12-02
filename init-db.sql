-- Ensure postgres role exists (should be created by default, but this is a safety net)
CREATE ROLE IF NOT EXISTS postgres WITH LOGIN SUPERUSER CREATEDB CREATEROLE PASSWORD 'postgres';
