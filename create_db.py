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

conn.commit()
conn.close()

print("Database created successfully.")
