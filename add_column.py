import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

cursor.execute("ALTER TABLE resumes ADD COLUMN file_type TEXT;")

conn.commit()
conn.close()
print("✔️ Column file_type added safely")
