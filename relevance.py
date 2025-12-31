import re

def compute_relevance(query: str, text: str) -> int:
    """
    ATS-style relevance scoring:
    - Boolean already passed (this only ranks)
    - First keyword = highest priority
    - Quoted phrases > single words
    - Presence > frequency (anti-spam)
    """

    if not query or not text:
        return 0

    text = text.lower()
    query = query.lower()

    # --- extract phrases ---
    phrases = re.findall(r'"([^"]+)"', query)

    # remove phrases from query before extracting words
    query_wo_phrases = re.sub(r'"[^"]+"', '', query)

    words = re.findall(r'\b[a-z0-9+.#-]+\b', query_wo_phrases)
    words = [w for w in words if w not in ("and", "or", "not")]

    score = 0
    weight = len(phrases) + len(words)

    # --- phrase priority (highest) ---
    for phrase in phrases:
        if phrase in text:
            score += weight * 20
        weight -= 1

    # --- word priority ---
    for word in words:
        if word in text:
            score += weight * 10
        weight -= 1

    return score
