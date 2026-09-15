-- 002_seed_test_data.sql
-- Executed second, within the workspace schema (search_path already set by the Job).

INSERT INTO babylon_test_table (label)
VALUES
    ('babylon-script-test-1'),
    ('babylon-script-test-2'),
    ('babylon-script-test-3')
ON CONFLICT DO NOTHING;
