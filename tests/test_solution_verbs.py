from tutor.solution_verbs import find_solution_verb

FLAGGED = [
    "A customer service phone line puts you through to a billing specialist when your question gets too complex.",
    "What would you want to happen so the right person takes over?",
    "How would you picture the first specialist handing the customer over to the second one?",
    "A routing assistant figures out which department they need.",
    "The receptionist needs to transfer them to a specialist.",
]

CLEAN = [
    "You are working on a puzzle and the piece in your hand needs sewing skills you do not have.",
    "Different specialized agents handle different tasks. What could go wrong if two disagree?",
    "A customer asks a complex question that the receptionist cannot answer. What would you want to happen next?",
    "What do you think the word handoff refers to?",
    "You forgot your password and cannot log in. What would you do?",
]


def test_solution_verbs_are_found():
    for text in FLAGGED:
        assert find_solution_verb(text), text


def test_clean_text_is_not_flagged():
    for text in CLEAN:
        assert find_solution_verb(text) is None, text