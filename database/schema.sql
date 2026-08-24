-- Run this SQL in your Supabase SQL Editor
-- First drop old tables:
-- DROP TABLE IF EXISTS tasks;
-- DROP TABLE IF EXISTS users;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE users (
    telegram_id BIGINT PRIMARY KEY,
    first_name TEXT,
    username TEXT,
    timezone TEXT DEFAULT 'Africa/Addis_Ababa',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE tasks (
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

CREATE INDEX idx_tasks_user ON tasks (telegram_id, status);

-- Disable RLS so the service role key can read/write freely
ALTER TABLE users DISABLE ROW LEVEL SECURITY;
ALTER TABLE tasks DISABLE ROW LEVEL SECURITY;
