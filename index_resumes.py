import os
import sqlite3
import logging
from datetime import datetime

import pdfplumber
from docx import Document
from docx.opc.exceptions import PackageNotFoundError

# ----------------------------
# CONFIG
# ----------------------------
DB_NAME = "database.db"

# Detect resume folder automatically
if os.path.exists("resumes"):
    RESUME_FOLDER = "resumes"            # Full dataset folder
else:
    RESUME_FOLDER = "sample_resumes"     # Small testing/demo folder

# Clean logs
logging.getLogger("pdfminer").setLevel(logging.ERROR)
logging.getLogger("pdfplumber").setLevel(logging.ERROR)


# ----------------------------
# TEXT EXTRACTION (SAFE)
# ----------------------------
def extract_text(file_path):
    text_chunks = []

    try:
        # 🟢 PDF Extraction
        if file_path.lower().endswith(".pdf"):
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    try:
                        page_text = page.extract_text()
                        if page_text and page_text.strip():
                            text_chunks.append(page_text)
                        else:
                            print(f"⚠️ No text found in {os.path.basename(file_path)} - Page {page_num}")
                    except Exception as e:
                        print(f"❌ Error on page {page_num} in {file_path}: {e}")
                        continue

        # 🟢 DOCX Extraction
        elif file_path.lower().endswith(".docx"):
            doc = Document(file_path)
            for para in doc.paragraphs:
                if para.text.strip():
                    text_chunks.append(para.text)

    except PackageNotFoundError:
        print(f"🚫 Corrupt DOCX skipped: {os.path.basename(file_path)}")
        return ""

    except Exception as e:
        print(f"🚫 Error reading {os.path.basename(file_path)}: {e}")
        return ""

    # Clean formatting
    full_text = " ".join(text_chunks)
    full_text = " ".join(full_text.split())
    return full_text.lower()


# ----------------------------
# DATABASE SETUP
# ----------------------------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS resumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT,
            file_path TEXT UNIQUE,
            content TEXT,
            modified_date TEXT,
            file_type TEXT
        )
    """)

    conn.commit()
    conn.close()


# ----------------------------
# INDEXING FUNCTION
# ----------------------------
def index_resumes():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    print(f"\n📁 Indexing from folder: {RESUME_FOLDER}\n")

    for file in os.listdir(RESUME_FOLDER):
        path = os.path.join(RESUME_FOLDER, file)

        if not os.path.isfile(path): 
            continue
        if file.startswith("~$"): 
            continue
        if not file.lower().endswith((".pdf", ".docx")): 
            continue

        # Skip huge files (optional)
        if os.path.getsize(path) > 10 * 1024 * 1024:  # > 10MB
            print(f"⛔ Skipping large file (>10MB): {file}")
            continue

        text = extract_text(path)
        if not text:
            print(f"⚠️ Skipped (no extractable text): {file}")
            continue

        modified_date = datetime.fromtimestamp(os.path.getmtime(path)).isoformat()
        file_type = os.path.splitext(file)[1].lower()

        cursor.execute("""
            INSERT OR REPLACE INTO resumes
            (file_name, file_path, content, modified_date, file_type)
            VALUES (?, ?, ?, ?, ?)
        """, (file, path, text, modified_date, file_type))

        print(f"✔️ Indexed: {file}")

    conn.commit()
    conn.close()


# ----------------------------
# MAIN
# ----------------------------
if __name__ == "__main__":
    init_db()
    index_resumes()
    print("\n🎉 DONE! Resume Indexing Completed Successfully\n")
