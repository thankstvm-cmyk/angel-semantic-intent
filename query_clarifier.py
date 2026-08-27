"""Conservative spelling clarification for supported ANGEL domains."""

import re
from difflib import get_close_matches


class QueryClarifier:
    """Suggest corrections only for known FTMS and authority-service terms."""

    DOMAIN_TERMS = (
        "accident", "ajman", "battery", "breakdown", "branch", "chiller",
        "database", "documents", "driver", "driving", "dubai", "emirates",
        "expiry", "fee", "fleet", "fuel", "fujairah", "heavy", "insurance",
        "maintenance", "mohre", "mulkiya", "office", "pedestrian", "permit",
        "police", "procedure", "registration", "renewal", "report", "road",
        "route", "rules", "service", "sharjah", "speed", "table", "traffic",
        "vehicle",
    )
    EXCLUDED_TERMS = {"rts"}  # Handled by the authority-specific RTA confirmation.

    def suggest(self, question):
        """Return a corrected query when a domain term has a high-confidence typo."""
        substitutions = []

        def replace(match):
            word = match.group(0)
            lowered = word.lower()
            if lowered in self.DOMAIN_TERMS or lowered in self.EXCLUDED_TERMS or len(lowered) < 4:
                return word
            candidate = get_close_matches(lowered, self.DOMAIN_TERMS, n=1, cutoff=0.84)
            if not candidate:
                return word
            corrected = candidate[0]
            substitutions.append((word, corrected))
            return corrected

        corrected_question = re.sub(r"[A-Za-z]+", replace, question)
        if not substitutions:
            return None
        return corrected_question, substitutions
