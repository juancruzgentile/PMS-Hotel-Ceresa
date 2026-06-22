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

CREATE TABLE IF NOT EXISTS guests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    guest_code TEXT NOT NULL UNIQUE,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,

    email TEXT,
    phone TEXT,
    nationality TEXT,
    notes TEXT,

    is_active INTEGER NOT NULL DEFAULT 1,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (is_active IN (0, 1))
);

CREATE TABLE IF NOT EXISTS reservations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    reservation_code TEXT NOT NULL UNIQUE,
    guest_id INTEGER NOT NULL,
    room_id INTEGER NOT NULL,

    check_in_date TEXT NOT NULL,
    check_out_date TEXT NOT NULL,

    status TEXT NOT NULL DEFAULT 'pending',

    adults INTEGER NOT NULL DEFAULT 1,
    children INTEGER NOT NULL DEFAULT 0,
    notes TEXT,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (guest_id)
        REFERENCES guests(id)
        ON DELETE RESTRICT,

    FOREIGN KEY (room_id)
        REFERENCES rooms(id)
        ON DELETE RESTRICT,

    CHECK (
        status IN (
            'pending',
            'confirmed',
            'checked_in',
            'checked_out',
            'cancelled'
        )
    ),

    CHECK (adults >= 1),
    CHECK (children >= 0),
    CHECK (check_out_date > check_in_date)
);
CREATE TABLE IF NOT EXISTS billing_accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    reservation_id INTEGER NOT NULL UNIQUE,
    status TEXT NOT NULL DEFAULT 'open',
    notes TEXT,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (reservation_id)
        REFERENCES reservations(id)
        ON DELETE RESTRICT,

    CHECK (
        status IN (
            'open',
            'closed',
            'cancelled'
        )
    )
);


CREATE TABLE IF NOT EXISTS billing_charges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    billing_account_id INTEGER NOT NULL,
    source_module TEXT NOT NULL,
    description TEXT NOT NULL,
    amount_cents INTEGER NOT NULL,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (billing_account_id)
        REFERENCES billing_accounts(id)
        ON DELETE RESTRICT,

    CHECK (amount_cents > 0)
);


CREATE TABLE IF NOT EXISTS billing_payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    billing_account_id INTEGER NOT NULL,
    payment_method TEXT NOT NULL,
    amount_cents INTEGER NOT NULL,
    reference TEXT,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (billing_account_id)
        REFERENCES billing_accounts(id)
        ON DELETE RESTRICT,

    CHECK (amount_cents > 0)
);


CREATE TABLE IF NOT EXISTS audit_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    module TEXT NOT NULL,
    event_type TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id INTEGER NOT NULL,

    reservation_id INTEGER,
    room_id INTEGER,
    billing_account_id INTEGER,
    actor_user_id INTEGER,

    before_state_json TEXT,
    after_state_json TEXT,
    metadata_json TEXT,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (reservation_id)
        REFERENCES reservations(id)
        ON DELETE RESTRICT,

    FOREIGN KEY (room_id)
        REFERENCES rooms(id)
        ON DELETE RESTRICT,

    FOREIGN KEY (billing_account_id)
        REFERENCES billing_accounts(id)
        ON DELETE RESTRICT,

    FOREIGN KEY (actor_user_id)
        REFERENCES users(id)
        ON DELETE RESTRICT
);
