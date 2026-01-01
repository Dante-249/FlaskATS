import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE resumes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_name TEXT,
    file_path TEXT,
    content TEXT,
    modified_date TEXT
)
""")

conn.commit()
conn.close()

print("✔️ database.db created with correct schema!")
