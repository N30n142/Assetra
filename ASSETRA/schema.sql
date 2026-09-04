-- Assetra database schema (plain SQL, SQLite dialect)

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS locations (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    name    TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS employees (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name       TEXT NOT NULL,
    email           TEXT UNIQUE,
    location_id     INTEGER,
    active          INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (location_id) REFERENCES locations(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS assets (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_tag           TEXT NOT NULL UNIQUE,      -- user-entered Asset ID, e.g. LAPTOP-001
    name                TEXT NOT NULL,
    category            TEXT NOT NULL DEFAULT 'Other',
    serial_number       TEXT,
    location_id         INTEGER,
    assigned_employee_id INTEGER,
    condition           TEXT NOT NULL DEFAULT 'Good',   -- New, Good, Fair, Poor, Damaged
    status              TEXT NOT NULL DEFAULT 'Available', -- Available, Assigned, In Repair, Retired, Lost
    purchase_date        TEXT,
    purchase_cost         REAL,
    vendor               TEXT,
    warranty_expiry       TEXT,
    notes                TEXT,
    created_at           TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at           TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (location_id) REFERENCES locations(id) ON DELETE SET NULL,
    FOREIGN KEY (assigned_employee_id) REFERENCES employees(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS maintenance_records (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id        INTEGER NOT NULL,
    service_date    TEXT NOT NULL,
    description     TEXT NOT NULL,
    cost            REAL,
    performed_by    TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS asset_history (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id        INTEGER NOT NULL,
    action          TEXT NOT NULL,     -- Created, Assigned, Unassigned, Transferred, Status Change, Condition Change, Edited, Maintenance
    details         TEXT,
    performed_by    TEXT,
    timestamp       TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_assets_status ON assets(status);
CREATE INDEX IF NOT EXISTS idx_assets_category ON assets(category);
CREATE INDEX IF NOT EXISTS idx_history_asset ON asset_history(asset_id);
CREATE INDEX IF NOT EXISTS idx_maintenance_asset ON maintenance_records(asset_id);