-- Run this SQL in your Supabase SQL Editor
-- DROP TABLE IF EXISTS tasks;
-- DROP TABLE IF EXISTS users;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS users (
    telegram_id BIGINT PRIMARY KEY,
    first_name TEXT,
    username TEXT,
    timezone TEXT DEFAULT 'Africa/Addis_Ababa',
    created_at TEXT DEFAULT (NOW() AT TIME ZONE 'Africa/Addis_Ababa')::TEXT
);

CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    telegram_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    due_datetime TEXT NOT NULL,
    reminder_datetime TEXT NOT NULL,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'reminded', 'completed', 'cancelled')),
    created_at TEXT DEFAULT (NOW() AT TIME ZONE 'Africa/Addis_Ababa')::TEXT,
    updated_at TEXT DEFAULT (NOW() AT TIME ZONE 'Africa/Addis_Ababa')::TEXT
);

CREATE INDEX IF NOT EXISTS idx_tasks_reminder ON tasks (reminder_datetime, status);
CREATE INDEX IF NOT EXISTS idx_tasks_user ON tasks (telegram_id, status);
