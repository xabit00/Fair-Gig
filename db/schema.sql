CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(120) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'worker'
        CHECK (role IN ('worker', 'verifier', 'advocate')),
    city_zone VARCHAR(80),
    category VARCHAR(40)
        CHECK (category IS NULL OR category IN ('ride_hailing', 'delivery', 'freelancing')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS shifts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    worker_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    platform VARCHAR(80) NOT NULL,
    date DATE NOT NULL,
    hours_worked NUMERIC(5, 2) NOT NULL CHECK (hours_worked > 0 AND hours_worked <= 24),
    gross_earned NUMERIC(12, 2) NOT NULL CHECK (gross_earned >= 0),
    deductions NUMERIC(12, 2) NOT NULL DEFAULT 0 CHECK (deductions >= 0),
    net_received NUMERIC(12, 2) NOT NULL CHECK (net_received >= 0),
    verification_status VARCHAR(30) NOT NULL DEFAULT 'pending'
        CHECK (verification_status IN ('pending', 'confirmed', 'discrepancy_flagged', 'unverifiable')),
    screenshot_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (net_received <= gross_earned),
    UNIQUE (worker_id, platform, date)
);

CREATE TABLE IF NOT EXISTS grievance_clusters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(160) NOT NULL,
    platform VARCHAR(80),
    category VARCHAR(80),
    status VARCHAR(20) NOT NULL DEFAULT 'open'
        CHECK (status IN ('open', 'monitoring', 'escalated', 'resolved')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS grievances (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    worker_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    platform VARCHAR(80) NOT NULL,
    category VARCHAR(80) NOT NULL,
    description TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'submitted'
        CHECK (status IN ('submitted', 'reviewing', 'escalated', 'resolved', 'closed')),
    cluster_id UUID REFERENCES grievance_clusters(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS grievance_tags (
    grievance_id UUID NOT NULL REFERENCES grievances(id) ON DELETE CASCADE,
    tag VARCHAR(60) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (grievance_id, tag)
);

CREATE TABLE IF NOT EXISTS refresh_tokens (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash CHAR(64) NOT NULL UNIQUE,
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_shifts_worker_date ON shifts (worker_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_shifts_platform_date ON shifts (platform, date DESC);
CREATE INDEX IF NOT EXISTS idx_grievances_worker ON grievances (worker_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_grievances_cluster ON grievances (cluster_id);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user ON refresh_tokens (user_id);

