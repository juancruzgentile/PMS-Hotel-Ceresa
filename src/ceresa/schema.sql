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

    CHECK (
        room_status IN (
            'available',
            'occupied',
            'out_of_service'
        )
    ),

    CHECK (
        cleaning_status IN (
            'clean',
            'dirty',
            'in_progress'
        )
    ),

    CHECK (
        maintenance_status IN (
            'ok',
            'needs_repair',
            'in_repair'
        )
    ),

    CHECK (has_jacuzzi IN (0, 1)),
    CHECK (has_balcony IN (0, 1))
);


CREATE TABLE IF NOT EXISTS departments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,

    is_active INTEGER NOT NULL DEFAULT 1,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (is_active IN (0, 1))
);


CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    username TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE,

    user_type TEXT NOT NULL,
    department_id INTEGER,

    is_active INTEGER NOT NULL DEFAULT 1,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (department_id)
        REFERENCES departments(id)
        ON DELETE RESTRICT,

    CHECK (
        user_type IN (
            'employee',
            'supervisor',
            'director',
            'guest'
        )
    ),

    CHECK (is_active IN (0, 1)),

    CHECK (
        (
            user_type IN ('employee', 'supervisor')
            AND department_id IS NOT NULL
        )
        OR
        (
            user_type IN ('director', 'guest')
            AND department_id IS NULL
        )
    )
);