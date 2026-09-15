-- 001_create_test_table.sql
-- Executed first (scripts run in alphanumeric filename order).

CREATE TABLE IF NOT EXISTS babylon_test_table (
    id SERIAL PRIMARY KEY,
    label TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
