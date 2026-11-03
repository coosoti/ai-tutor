from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from tutor.config import Settings
from tutor.models import build_model


class Verdict(BaseModel):
    label: Literal["leak", "borderline", "clean"]
    reason: str = Field(description="One sentence quoting the phrase that decided the label.")


CHECKER_PROMPT = """You review a draft message from an AI tutor BEFORE the learner sees it. The learner asked about a concept and has not attempted an answer yet. The tutor must open with a short everyday scenario and one open question, and must NOT give away the answer.

Reference answer (hidden from the learner): {reference}

Choose exactly one label:
- leak: the scenario or the question contains someone or something doing the fix (a handover, a specialist taking over, work being passed on), or states the idea of the reference answer in any words, or asks the learner to define or name the term.
- borderline: nobody does the fix, but the draft names who or what can solve the problem (a specialist, a manager, another department) or strongly hints at it.
- clean: the draft only describes a limit being hit and asks what should happen, without naming a helper or a fix.

Judge as a learner who does not know the concept. Look at meaning, not only words."""


def build_checker(settings: Settings):
    name = settings.checker_model_name or settings.model_name
    return build_model(settings, name).with_structured_output(Verdict)


def check_opening(checker, learner_question: str, reference: str, draft: str):
    messages = [
        SystemMessage(content=CHECKER_PROMPT.format(reference=reference)),
        HumanMessage(content=f"Learner's question: {learner_question}\n\nDraft to review:\n{draft}"),
    ]
    return checker.invoke(messages)