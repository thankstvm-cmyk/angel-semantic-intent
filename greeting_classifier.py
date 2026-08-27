"""Semantic greeting classification for ANGEL's top-level message routing."""

import re


class GreetingClassifier:
    """Classify greeting-like messages before task routing or fallback."""

    BASIC_GREETINGS = (
        "hi", "hai", "hello", "hey", "yo", "salam", "assalamualaikum",
    )
    WELLBEING_PATTERNS = (
        "how are you", "how do you do", "you good",
    )
    TIME_GREETINGS = ("morning", "afternoon", "evening")
    FAREWELLS = ("bye", "goodbye", "good night", "see you", "thanks bye")
    TASK_PATTERNS = (
        ("documents", r"\b(?:doc|docs|document|documents|paper|papers)\b"),
        ("requirements", r"\b(?:required|required docs|requirement|requirements)\b"),
        ("renewal", r"\b(?:renew|renewal)\b"),
        ("mulkiya", r"\bmulkiya\b"),
        ("registration", r"\bregistration\b"),
        ("chiller", r"\bchiller\b"),
        ("passing", r"\bpassing\b"),
        ("permit", r"\bpermit\b"),
        ("fee", r"\b(?:fee|fees|cost|price|charge)\b"),
        ("status", r"\bstatus\b"),
        ("process", r"\bprocess\b"),
        ("steps", r"\bsteps?\b"),
    )
    TYPO_FOLDS = (
        (r"\bhellow\b", "hello"),
        (r"\bhelo\b", "hello"),
        (r"\bhallo\b", "hello"),
        (r"\bgud\b", "good"),
        (r"\bgd\b", "good"),
        (r"\bafter\s+noon\b", "afternoon"),
        (r"\bmornin\b", "morning"),
        (r"\bhw\s+r\s+u\b", "how are you"),
        (r"\bhow\s+r\s+u\b", "how are you"),
    )
    OPENING_PATTERNS = (
        r"^(?:hi|hai|hello|hellow|helo|hallo|hey|yo|salam|assalamualaikum)\b[\s,;:!\-.]*",
        r"^(?:good\s+morning|morning|good\s+afternoon|good\s+after\s+noon|afternoon|good\s+evening|evening)\b[\s,;:!\-.]*",
        r"^(?:how\s+are\s+you|how\s+do\s+you\s+do|how\s+r\s+u|hw\s+r\s+u|you\s+good)\b[\s,;:!\-.]*",
    )

    def classify(self, question):
        original = (question or "").strip()
        normalized = self.normalize(original)
        detected_task_tokens = self._detect_task_tokens(normalized)
        greeting_tokens = self._detect_greeting_tokens(normalized)
        task_text = self.extract_task_text(original)

        if greeting_tokens and detected_task_tokens and task_text:
            confidence = 0.92 if self._starts_with_greeting(normalized) else 0.78
            return self._result(
                "greeting_plus_task",
                confidence,
                normalized,
                greeting_tokens,
                detected_task_tokens,
                True,
                "greeting.plus_task",
                task_text,
            )

        if self._matches_any(normalized, self.WELLBEING_PATTERNS):
            confidence = 0.95 if "how are you" in normalized or "how do you do" in normalized else 0.76
            return self._result(
                "wellbeing_query",
                confidence,
                normalized,
                ["how are you" if "how are you" in normalized else "how do you do" if "how do you do" in normalized else "you good"],
                detected_task_tokens,
                False,
                "greeting.wellbeing",
                task_text,
            )

        time_token = self._time_token(normalized)
        if time_token:
            confidence = 0.90 if f"good {time_token}" in normalized else 0.82
            return self._result(
                "time_greeting",
                confidence,
                normalized,
                [time_token],
                detected_task_tokens,
                False,
                f"greeting.time.{time_token}",
                task_text,
            )

        basic_token = self._basic_token(normalized)
        if basic_token:
            confidence = 0.90 if len(normalized.split()) <= 3 else 0.76
            return self._result(
                "basic_greeting",
                confidence,
                normalized,
                [basic_token],
                detected_task_tokens,
                False,
                "greeting.basic",
                task_text,
            )

        farewell_token = self._farewell_token(normalized)
        if farewell_token:
            return self._result(
                "farewell",
                0.88,
                normalized,
                [farewell_token],
                detected_task_tokens,
                False,
                "greeting.farewell",
                task_text,
            )

        return self._result("non_greeting", 0.0, normalized, greeting_tokens, detected_task_tokens, False, "greeting.none", task_text)

    def normalize(self, question):
        text = re.sub(r"([a-z])\1{2,}", r"\1\1", (question or "").lower())
        for pattern, replacement in self.TYPO_FOLDS:
            text = re.sub(pattern, replacement, text)
        text = re.sub(r"[^\w\s]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def extract_task_text(self, question):
        text = (question or "").strip()
        for pattern in self.OPENING_PATTERNS:
            updated = re.sub(pattern, "", text, count=1, flags=re.I)
            if updated != text:
                text = updated
                break
        return text.lstrip(" ,;:!?-.")

    @staticmethod
    def _threshold_band(confidence):
        if confidence >= 0.75:
            return "high"
        if confidence >= 0.50:
            return "medium"
        return "low"

    @staticmethod
    def _matches_any(text, patterns):
        return any(pattern in text for pattern in patterns)

    def _time_token(self, text):
        return next((token for token in self.TIME_GREETINGS if re.search(rf"\b{token}\b", text)), None)

    def _basic_token(self, text):
        return next((token for token in self.BASIC_GREETINGS if re.search(rf"\b{re.escape(token)}\b", text)), None)

    def _farewell_token(self, text):
        return next((token for token in self.FAREWELLS if token in text), None)

    def _detect_task_tokens(self, text):
        detected = []
        for token, pattern in self.TASK_PATTERNS:
            if re.search(pattern, text):
                detected.append(token)
        return detected

    def _detect_greeting_tokens(self, text):
        detected = []
        basic = self._basic_token(text)
        if basic:
            detected.append(basic)
        time_token = self._time_token(text)
        if time_token:
            detected.append(time_token)
        if self._matches_any(text, self.WELLBEING_PATTERNS):
            detected.append("how are you" if "how are you" in text else "how do you do" if "how do you do" in text else "you good")
        farewell = self._farewell_token(text)
        if farewell:
            detected.append(farewell)
        return detected

    def _starts_with_greeting(self, text):
        return any(re.match(pattern, text, re.I) for pattern in self.OPENING_PATTERNS)

    def _result(
        self,
        classification,
        confidence,
        normalized_text,
        detected_greeting_tokens,
        detected_task_tokens,
        should_invoke_task_engine,
        response_template_key,
        task_text,
    ):
        threshold_band = self._threshold_band(confidence)
        if threshold_band == "low":
            classification = "non_greeting"
            should_invoke_task_engine = False
            response_template_key = "greeting.none"
        return {
            "class": classification,
            "confidence": confidence,
            "threshold_band": threshold_band,
            "normalized_text": normalized_text,
            "detected_greeting_tokens": detected_greeting_tokens,
            "detected_task_tokens": detected_task_tokens,
            "should_invoke_task_engine": should_invoke_task_engine,
            "response_template_key": response_template_key,
            "hard_fail": False,
            "task_text": task_text,
        }
