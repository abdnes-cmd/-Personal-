CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    section TEXT,        -- يحدد: 'مسجد' أو 'شخصي'
    type TEXT,           -- يحدد: 'إيراد' أو 'مصروف'
    category TEXT,       -- رواتب، صيانة، تبرعات، شخصي...
    amount REAL,
    notes TEXT
);
