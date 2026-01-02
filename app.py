from flask import Flask, render_template, request, send_from_directory
import sqlite3
import re
import os
from markupsafe import Markup
from docx import Document

# Detect Render environment
IS_RENDER = os.environ.get("RENDER") == "true"

# Only import textract for local environment
if not IS_RENDER:
    try:
        import textract  # for .doc files locally
    except ImportError:
        textract = None

from boolean_engine import evaluate_boolean
from relevance import compute_relevance

# ========================
# CONFIG
# ========================

# Choose folder and DB based on environment
if os.path.exists("resumes") and not IS_RENDER:
    RESUME_FOLDER = "resumes"            
    DB_NAME = "database.db"             # full ATS DB
else:
    RESUME_FOLDER = "sample_resumes"
    DB_NAME = "sample_db.db"            # sample DB for faster search

app = Flask(__name__)

# ========================
# HELPER FUNCTION
# ========================

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
        # On Render, skip content for .doc
        if not IS_RENDER and textract:
            try:
                return textract.process(path).decode("utf-8")
            except:
                return ""
        else:
            return ""
    
    return ""

# ========================
# JINJA FILTER
# ========================

@app.template_filter("highlight_keywords")
def highlight_keywords(text, query):
    if not text or not query:
        return text

    keywords = re.findall(r'"([^"]+)"|\w+', query.lower())
    keywords = [k for k in keywords if k and k not in ("and", "or", "not")]

    highlighted = text
    for word in keywords:
        pattern = re.compile(re.escape(word), re.IGNORECASE)
        highlighted = pattern.sub(
            lambda m: f"<span style='background:#fff3a0'>{m.group(0)}</span>",
            highlighted
        )
    return Markup(highlighted)

# ========================
# ROUTES
# ========================

@app.route("/", methods=["GET", "POST"])
def index():
    matches = []
    boolean_query = ""

    if request.method == "POST":
        boolean_query = request.form.get("boolean_query", "").strip()

        # ------------------------
        # Use database for both sample and local resumes
        # ------------------------
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT file_name, file_path, content, modified_date FROM resumes"
        )
        rows = cursor.fetchall()
        conn.close()

        for file_name, file_path, content, modified_date in rows:
            if boolean_query:
                # Only search if content exists
                if content and evaluate_boolean(boolean_query, content):
                    score = compute_relevance(boolean_query, content)
                    matches.append((file_name, file_path, modified_date, score))
            else:
                matches.append((file_name, file_path, modified_date, 0))

        # Sort by relevance first → recent second
        matches.sort(key=lambda x: (x[3], x[2]), reverse=True)

    return render_template(
        "index.html",
        matches=matches,
        query=boolean_query
    )

# ========================
# SERVE RESUME FILES
# ========================

@app.route("/resume/<path:filename>")
def serve_resume(filename):
    return send_from_directory(RESUME_FOLDER, filename)

# ========================
# ATS ARCHITECTURE VISUAL
# ========================

@app.route("/architecture")
def architecture():
    # Make sure template filename matches exactly (Architecture.html)
    return render_template("Architecture.html")

# ========================
# START APP
# ========================

if __name__ == "__main__":
    app.run(debug=True)
