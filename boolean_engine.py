import re


class BooleanSearchError(Exception):
    pass


def normalize_query(query: str) -> str:
    """
    Normalize query:
    - Lowercase words
    - Uppercase boolean operators
    - Clean extra spaces
    """
    query = query.strip().lower()

    # Normalize boolean operators to uppercase
    query = re.sub(r'\b(and|or|not)\b', lambda m: m.group(1).upper(), query)

    return query


def tokenize(query: str):
    """
    Tokenize query into:
    - Words
    - Boolean operators
    - Parentheses
    - Quoted phrases
    """
    # Extract quoted phrases
    phrases = re.findall(r'"([^"]+)"', query)
    phrase_map = {}

    for i, phrase in enumerate(phrases):
        token = f"__PHRASE_{i}__"
        phrase_map[token] = phrase.lower()
        query = query.replace(f'"{phrase}"', token)

    tokens = re.findall(
        r'\(|\)|AND|OR|NOT|__PHRASE_\d+__|[a-zA-Z0-9_+.#-]+',
        query
    )

    return tokens, phrase_map


def to_rpn(tokens):
    """
    Convert tokens to Reverse Polish Notation using Shunting Yard
    """
    output = []
    stack = []

    precedence = {
        "OR": 1,
        "AND": 2,
        "NOT": 3
    }

    for token in tokens:
        if token not in precedence and token not in ("(", ")"):
            output.append(token)

        elif token == "(":
            stack.append(token)

        elif token == ")":
            while stack and stack[-1] != "(":
                output.append(stack.pop())
            if not stack:
                raise BooleanSearchError("Mismatched parentheses")
            stack.pop()

        else:  # operator
            while (
                stack and
                stack[-1] != "(" and
                precedence.get(stack[-1], 0) >= precedence[token]
            ):
                output.append(stack.pop())
            stack.append(token)

    while stack:
        if stack[-1] == "(":
            raise BooleanSearchError("Mismatched parentheses")
        output.append(stack.pop())

    return output


def evaluate_rpn(rpn, text, phrase_map):
    """
    Evaluate RPN expression against resume text
    """
    stack = []
    text = text.lower()

    def check(token):
        if token in phrase_map:
            return phrase_map[token] in text
        return token in text

    for token in rpn:
        if token == "NOT":
            if not stack:
                raise BooleanSearchError("NOT operator missing operand")
            stack.append(not stack.pop())

        elif token in ("AND", "OR"):
            if len(stack) < 2:
                raise BooleanSearchError(f"{token} operator missing operands")
            b = stack.pop()
            a = stack.pop()
            stack.append(a and b if token == "AND" else a or b)

        else:
            stack.append(check(token))

    if len(stack) != 1:
        raise BooleanSearchError("Invalid boolean expression")

    return stack[0]


def evaluate_boolean(query: str, text: str) -> bool:
    """
    Professional boolean search evaluator.
    Safe and ATS-ready.
    """
    if not query or not text:
        return False

    try:
        query = normalize_query(query)
        tokens, phrase_map = tokenize(query)
        rpn = to_rpn(tokens)
        return evaluate_rpn(rpn, text, phrase_map)

    except BooleanSearchError:
        # Invalid queries should NOT break ATS
        return False


# ======================
# TESTING (SAFE TO REMOVE)
# ======================
if __name__ == "__main__":
    resumes = [
        "John has CISSP and CCIE certifications and Python experience",
        "Alice is a Network Engineer with CCIE",
        "Bob is a Python Developer with Flask",
        "DevOps Engineer with AWS and Kubernetes"
    ]

    queries = [
        "CISSP AND CCIE",
        "CISSP or CCIE",
        "python AND developer",
        '"network engineer"',
        "python AND NOT django",
        "(CISSP OR CCIE) AND python",
        "aws AND (kubernetes OR docker)",
        "NOT java"
    ]

    for q in queries:
        print(f"\nQuery: {q}")
        for r in resumes:
            if evaluate_boolean(q, r):
                print(" ✔", r)
