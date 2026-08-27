"""Common contract for every ANGEL capability."""

from abc import ABC, abstractmethod


class AngelEngine(ABC):
    """A modular ANGEL capability selected by ``IntentRouter``.

    Engines must be side-effect free unless their name and response explicitly
    describe an approved FTMS action.  This makes query engines safe to run in
    any order and gives a future LLM detector a stable list of capabilities.
    """

    name = ""
    priority = 50

    @abstractmethod
    def can_answer(self, question):
        """Return whether this engine owns the normalized user request."""

    @abstractmethod
    def answer(self, question):
        """Return a user-facing answer, or ``None`` when not applicable."""
