"""SQL DDL schema definitions and migrations for PLUS-ULTRA."""

from __future__ import annotations

CURRENT_SCHEMA_VERSION = 2

MIGRATION_V1_SQL = """
-- Categories table (reusable across tasks and features)
CREATE TABLE IF NOT EXISTS categories (
    id         TEXT PRIMARY KEY,
    name       TEXT NOT NULL,
    color      TEXT DEFAULT '#4a5568',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    synced_at  TEXT,
    is_deleted INTEGER NOT NULL DEFAULT 0
);

-- Partial index: allow reusing category names if previous one was soft-deleted
CREATE UNIQUE INDEX IF NOT EXISTS idx_categories_name_active
    ON categories(name) WHERE is_deleted = 0;

-- Tasks table with priority, labels, pace, and cloud readiness
CREATE TABLE IF NOT EXISTS tasks (
    id             TEXT PRIMARY KEY,
    category_id    TEXT REFERENCES categories(id) ON DELETE SET NULL,
    title          TEXT NOT NULL CHECK(length(trim(title)) > 0),
    description    TEXT DEFAULT '',
    due_date       TEXT,
    status         TEXT NOT NULL DEFAULT 'Pending'
                   CHECK(status IN (
                       'Pending', 'In Progress', 'Completed', 'Overdue'
                   )),
    task_label     TEXT DEFAULT 'College',
    critical_level TEXT NOT NULL DEFAULT 'Medium'
                   CHECK(critical_level IN ('High', 'Medium', 'Low')),
    pace_level     TEXT NOT NULL DEFAULT 'Short-term'
                   CHECK(pace_level IN ('Long-term', 'Short-term')),
    is_google_task INTEGER NOT NULL DEFAULT 0 CHECK(is_google_task IN (0, 1)),
    created_at     TEXT NOT NULL,
    updated_at     TEXT NOT NULL,
    synced_at      TEXT,
    is_deleted     INTEGER NOT NULL DEFAULT 0
);

-- Reminders table linked to tasks
CREATE TABLE IF NOT EXISTS reminders (
    id         TEXT PRIMARY KEY,
    task_id    TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    remind_at  TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    synced_at  TEXT,
    is_deleted INTEGER NOT NULL DEFAULT 0
);

-- Partial index: scheduler queries active reminders
CREATE INDEX IF NOT EXISTS idx_reminders_due
    ON reminders(remind_at) WHERE is_deleted = 0;

-- Local-only table: reminder fired state is device-specific
CREATE TABLE IF NOT EXISTS reminder_fires (
    reminder_id TEXT PRIMARY KEY REFERENCES reminders(id) ON DELETE CASCADE,
    fired_at    TEXT NOT NULL
);

-- machine-written state only (widget_x, widget_y, last_synced_at);
-- user preferences live only in user-settings.json
CREATE TABLE IF NOT EXISTS app_state (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""

MIGRATION_V2_SQL = """
-- Code tab items (snippets, commands, syntax, DSA problems)
CREATE TABLE IF NOT EXISTS code_items (
    id         TEXT PRIMARY KEY,
    category   TEXT NOT NULL,
    title      TEXT NOT NULL,
    content    TEXT NOT NULL DEFAULT '',
    language   TEXT DEFAULT 'python',
    difficulty TEXT DEFAULT 'Easy',
    is_done    INTEGER NOT NULL DEFAULT 0,
    url        TEXT DEFAULT '',
    notes      TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    synced_at  TEXT,
    is_deleted INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_code_items_cat
    ON code_items(category) WHERE is_deleted = 0;

-- Courses tab tracker
CREATE TABLE IF NOT EXISTS courses (
    id                TEXT PRIMARY KEY,
    title             TEXT NOT NULL,
    platform          TEXT DEFAULT 'Coursera',
    instructor        TEXT DEFAULT '',
    total_modules     INTEGER NOT NULL DEFAULT 10,
    completed_modules INTEGER NOT NULL DEFAULT 0,
    url               TEXT DEFAULT '',
    notes             TEXT DEFAULT '',
    created_at        TEXT NOT NULL,
    updated_at        TEXT NOT NULL,
    synced_at         TEXT,
    is_deleted        INTEGER NOT NULL DEFAULT 0
);

-- Ideas and Doubts tab items
CREATE TABLE IF NOT EXISTS ideas_doubts (
    id                TEXT PRIMARY KEY,
    kind              TEXT NOT NULL,
    title             TEXT NOT NULL,
    description       TEXT DEFAULT '',
    tech_stack_or_ref TEXT DEFAULT '',
    status            TEXT NOT NULL DEFAULT 'Idea',
    created_at        TEXT NOT NULL,
    updated_at        TEXT NOT NULL,
    synced_at         TEXT,
    is_deleted        INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_ideas_doubts_kind
    ON ideas_doubts(kind, status) WHERE is_deleted = 0;

-- Opportunities tab items (internships, jobs, hackathons)
CREATE TABLE IF NOT EXISTS opportunities (
    id           TEXT PRIMARY KEY,
    title        TEXT NOT NULL,
    organization TEXT NOT NULL,
    kind         TEXT NOT NULL DEFAULT 'Internship',
    url          TEXT DEFAULT '',
    deadline     TEXT DEFAULT '',
    status       TEXT NOT NULL DEFAULT 'Saved',
    notes        TEXT DEFAULT '',
    created_at   TEXT NOT NULL,
    updated_at   TEXT NOT NULL,
    synced_at    TEXT,
    is_deleted   INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_opportunities_kind
    ON opportunities(kind, status) WHERE is_deleted = 0;

-- Quick Links launcher
CREATE TABLE IF NOT EXISTS quick_links (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    target_uri  TEXT NOT NULL,
    category    TEXT NOT NULL DEFAULT 'Web',
    click_count INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL,
    synced_at   TEXT,
    is_deleted  INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_quick_links_cat
    ON quick_links(category) WHERE is_deleted = 0;
"""
