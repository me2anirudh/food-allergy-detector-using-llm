import sqlite3

conn = sqlite3.connect("models/users.db")
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    allergies TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS scan_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    product_name TEXT NOT NULL,
    ingredients TEXT,
    result TEXT NOT NULL,  -- 'SAFE' or 'UNSAFE'
    allergens_found TEXT,  -- comma-separated
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id),
    UNIQUE(user_id, product_name)
)
""")

conn.commit()
conn.close()

print("Database created successfully.")
