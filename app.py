from flask import Flask, render_template, request, send_from_directory
import sqlite3
import re
import os
from markupsafe import Markup
from docx import Document
import textract  # for .doc files

from boolean_engine import evaluate_boolean
from relevance import compute_relevance


# ========================
# CONFIG (MUST BE AT TOP)
# ========================

DB_NAME = "database.db"

# Detect Render environment
IS_RENDER = os.environ.get("RENDER") == "true"

# Automatically choose folder:
# - If "resumes/" exists → use PRIVATE DATA (local only)
# - Else → use "sample_resumes/" (GitHub demo)
if os.path.exists("resumes") and not IS_RENDER:
    RESUME_FOLDER = "resumes"            # Local private resumes
else:
    RESUME_FOLDER = "sample_resumes"     # Demo folder for GitHub

app = Flask(__name__)


# ========================
# HELPER FUNCTION TO READ FILE CONTENT
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
            full_text = [para.text for para in doc.paragraphs]
            return "\n".join(full_text)
        except:
            return ""
    
    elif ext == "doc":
        try:
            return textract.process(path).decode("utf-8")
        except:
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
        # Public demo: read from sample_resumes folder
        # ------------------------
        if IS_RENDER or RESUME_FOLDER == "sample_resumes":
            for file_name in os.listdir(RESUME_FOLDER):
                path = os.path.join(RESUME_FOLDER, file_name)
                if file_name.lower().endswith((".txt", ".docx", ".doc")):
                    content = read_file_content(path)
                    # Apply boolean search
                    if boolean_query and evaluate_boolean(boolean_query, content):
                        score = compute_relevance(boolean_query, content)
                        matches.append((file_name, path, os.path.getmtime(path), score))
                    elif not boolean_query:
                        matches.append((file_name, path, os.path.getmtime(path), 0))

            # Sort by relevance first → recent second (for demo, score is 0 if no query)
            matches.sort(key=lambda x: (x[3], x[2]), reverse=True)

        # ------------------------
        # Local full ATS: use database
        # ------------------------
        else:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT file_name, file_path, content, modified_date FROM resumes"
            )
            rows = cursor.fetchall()
            conn.close()

            for file_name, file_path, content, modified_date in rows:
                if boolean_query and evaluate_boolean(boolean_query, content):
                    score = compute_relevance(boolean_query, content)
                    matches.append((file_name, file_path, modified_date, score))

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
    return render_template("architecture.html")


# ========================
# START APP
# ========================

if __name__ == "__main__":
    app.run(debug=True)
