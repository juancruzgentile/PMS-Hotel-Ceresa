PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS rooms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    room_number TEXT NOT NULL UNIQUE,
    floor INTEGER NOT NULL,
    room_type TEXT NOT NULL,

    room_status TEXT NOT NULL DEFAULT 'available',
    cleaning_status TEXT NOT NULL DEFAULT 'clean',
    maintenance_status TEXT NOT NULL DEFAULT 'ok',

    has_jacuzzi INTEGER NOT NULL DEFAULT 0,
    has_balcony INTEGER NOT NULL DEFAULT 0,
    notes TEXT,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (room_status IN ('available', 'occupied', 'out_of_service')),
    CHECK (cleaning_status IN ('clean', 'dirty', 'in_progress')),
    CHECK (maintenance_status IN ('ok', 'needs_repair', 'in_repair')),
    CHECK (has_jacuzzi IN (0, 1)),
    CHECK (has_balcony IN (0, 1))
);