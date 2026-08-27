"""Short-lived conversation context for precise ANGEL follow-up handling."""

import re


class ConversationContext:
    """Keeps only the last successful capability for the current chat window."""

    FOLLOW_UP_PATTERN = re.compile(
        r"^\s*(?:can you |could you |please )?(?:show|list|explain|describe|tell me more about)\s+"
        r"(?:them|those|these|it|that)\s*[?.!]*\s*$",
        re.I,
    )
    CONTEXTUAL_ENGINES = {"database"}

    def __init__(self):
        self.last_engine = None
        self.pending_authority = None
        self.pending_correction = None

    def resolve(self, question, detected_engine):
        """Prefer the prior topic only for an explicit short follow-up."""
        if self.last_engine in self.CONTEXTUAL_ENGINES and self.FOLLOW_UP_PATTERN.match(question):
            return self.last_engine
        return detected_engine

    def record(self, engine_name, answer):
        if answer and engine_name in self.CONTEXTUAL_ENGINES:
            self.last_engine = engine_name

    def set_pending_authority(self, authority):
        self.pending_authority = authority

    def consume_authority_confirmation(self, question):
        if self.pending_authority and question.lower().strip() in {"yes", "y", "yes please", "please"}:
            authority = self.pending_authority
            self.pending_authority = None
            return authority
        return None

    def set_pending_correction(self, corrected_question):
        self.pending_correction = corrected_question

    def consume_correction_confirmation(self, question):
        if not self.pending_correction:
            return None
        response = question.lower().strip()
        if response in {"yes", "y", "yes please", "please"}:
            corrected_question = self.pending_correction
            self.pending_correction = None
            return corrected_question
        if response in {"no", "n", "no thanks"}:
            self.pending_correction = None
            return ""
        return None
