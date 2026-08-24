-- Run this SQL in your Supabase SQL Editor
-- First: DROP TABLE IF EXISTS tasks; DROP TABLE IF EXISTS users;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS users (
    telegram_id BIGINT PRIMARY KEY,
    first_name TEXT,
    username TEXT,
    timezone TEXT DEFAULT 'Africa/Addis_Ababa',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

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

CREATE INDEX IF NOT EXISTS idx_tasks_user ON tasks (telegram_id, status);
