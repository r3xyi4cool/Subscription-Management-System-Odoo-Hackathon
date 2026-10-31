-- Migration: 009_notification_table.sql
-- Description: In-app notification system replacing email notifications
-- Scope: D1/D4/M8 local communications & event notifications

CREATE TABLE IF NOT EXISTS notification (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id BIGINT REFERENCES auth(id) ON DELETE CASCADE,
    customer_id BIGINT REFERENCES customer(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    type VARCHAR(50) NOT NULL DEFAULT 'system',
    link_url VARCHAR(255),
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    dedupe_key VARCHAR(255) UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_notification_user_read_created ON notification(user_id, is_read, created_at);
CREATE INDEX IF NOT EXISTS idx_notification_customer_read_created ON notification(customer_id, is_read, created_at);
CREATE INDEX IF NOT EXISTS ix_notification_dedupe_key ON notification(dedupe_key);

