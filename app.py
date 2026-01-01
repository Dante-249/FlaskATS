from flask import Flask, render_template, request, send_from_directory
import sqlite3
import re
import os
from markupsafe import Markup

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
                # Only read supported files for demo
                if file_name.lower().endswith((".txt", ".pdf", ".docx")):
                    content = ""  # For demo, no parsing yet
                    if boolean_query:
                        # Optionally skip relevance in demo
                        score = 0
                        matches.append((file_name, path, os.path.getmtime(path), score))
                    else:
                        matches.append((file_name, path, os.path.getmtime(path), 0))

            # Sort by modification date (most recent first)
            matches.sort(key=lambda x: x[2], reverse=True)

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
