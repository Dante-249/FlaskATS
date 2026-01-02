import sqlite3
import os
from docx import Document

# Detect Render environment
import os
IS_RENDER = os.environ.get("RENDER") == "true"

# Only import textract locally
if not IS_RENDER:
    try:
        import textract
    except ImportError:
        textract = None

DB_NAME = "sample_db.db"
RESUME_FOLDER = "sample_resumes"

# Helper function to read content
def read_file_content(path):
    ext = path.lower().split(".")[-1]

    if ext == "txt":
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except:
            return ""
    
    elif ext == "docx":
        try:
            doc = Document(path)
            return "\n".join([p.text for p in doc.paragraphs])
        except:
            return ""
    
    elif ext == "doc":
        if not IS_RENDER and textract:
            try:
                return textract.process(path).decode("utf-8")
            except:
                return ""
        else:
            # On Render, we skip .doc content
            return ""
    
    return ""

# Create/connect DB
conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

# Create table if it doesn't exist
cursor.execute("""
CREATE TABLE IF NOT EXISTS resumes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_name TEXT,
    file_path TEXT,
    file_type TEXT,
    content TEXT,
    modified_date REAL
)
""")

# Clear old data safely
cursor.execute("DELETE FROM resumes")

# Index all files in sample_resumes
for file_name in os.listdir(RESUME_FOLDER):
    path = os.path.join(RESUME_FOLDER, file_name)
    if file_name.lower().endswith((".txt", ".docx", ".doc")):
        content = read_file_content(path)
        file_type = file_name.split(".")[-1].lower()
        modified_date = os.path.getmtime(path)
        cursor.execute(
            "INSERT INTO resumes (file_name, file_path, file_type, content, modified_date) VALUES (?, ?, ?, ?, ?)",
            (file_name, path, file_type, content, modified_date)
        )

conn.commit()
conn.close()
print(f"✅ Sample resumes indexed into {DB_NAME}")
