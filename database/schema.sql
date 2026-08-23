-- Run this SQL in your Supabase SQL Editor

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE IF NOT EXISTS users (
    telegram_id BIGINT PRIMARY KEY,
    first_name TEXT,
    username TEXT,
    timezone TEXT DEFAULT 'Africa/Addis_Ababa',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tasks table
-- All times stored as TIMESTAMPTZ in UTC (Postgres converts on insert)
-- The code always sends UTC times, and displays in Addis Ababa time (UTC+3)
CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    telegram_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    due_datetime TIMESTAMPTZ NOT NULL,
    reminder_datetime TIMESTAMPTZ NOT NULL,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'reminded', 'completed', 'cancelled')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Fast lookups for the scheduler
CREATE INDEX IF NOT EXISTS idx_tasks_reminder ON tasks (reminder_datetime, status);
CREATE INDEX IF NOT EXISTS idx_tasks_user ON tasks (telegram_id, status);

-- IMPORTANT: If you already have a tasks table, drop and recreate it
-- to fix any bad data from before:
-- DROP TABLE IF EXISTS tasks;
-- Then re-run the CREATE TABLE above.
