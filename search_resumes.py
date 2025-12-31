import sqlite3

from boolean_engine import evaluate_boolean
from relevance import compute_relevance

DB_NAME = "database.db"


def search_resumes(boolean_query):
    """
    Returns resumes ordered by relevance score (highest first)
    """

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT file_name, file_path, content, modified_date FROM resumes"
    )

    matches = []

    for file_name, file_path, content, modified_date in cursor.fetchall():

        # 1️⃣ Boolean filter
        if boolean_query and not evaluate_boolean(boolean_query, content):
            continue

        # 2️⃣ Relevance score
        score = compute_relevance(boolean_query, content)

        matches.append(
            (file_name, file_path, modified_date, score)
        )

    conn.close()

    # 3️⃣ Sort by relevance score (DESC)
    matches.sort(key=lambda x: x[3], reverse=True)

    return matches


# 🔹 Standalone testing
if __name__ == "__main__":
    query = '("spring boot" OR springboot) AND java AND NOT sales'

    results = search_resumes(query)

    for r in results:
        print(f"{r[0]} | score={r[3]} | modified={r[2]}")

