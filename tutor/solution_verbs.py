import re

SOLUTION_VERBS = re.compile(
    r"\b(puts? (\w+ ){0,2}through|"
    r"pass(es|ed|ing)?\b|transfer\w*|"
    r"hand(s|ed|ing)? (\w+ ){0,2}(over|off)\b|"
    r"take[sn]? over|taking over|"
    r"rout(e|es|ed|ing)\b|escalat\w*|"
    r"forward(s|ed|ing)?\b|redirect\w*|step\w* aside|bring\w* in)",
    re.IGNORECASE,
)


def find_solution_verb(text):
    match = SOLUTION_VERBS.search(text)
    return match.group(0) if match else None