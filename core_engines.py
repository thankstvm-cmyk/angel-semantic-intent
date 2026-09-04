"""Production engines composed by ANGEL's single intent router."""

import re

from .engine_contract import AngelEngine
from .ftms_knowledge import FTMSKnowledge
from .mathematics_engine import MathematicsEngine
from .operations_engine import ActionRouter, ApprovedInternetLookup


def _contains(text, phrases):
    return any(re.search(r"\b" + re.escape(phrase) + r"\b", text) for phrase in phrases)


class ConversationEngine(AngelEngine):
    name = "conversation"
    priority = 100
    KEYWORDS = (
        "hi", "hai", "hello", "hey", "good morning", "good afternoon", "good evening",
        "how are you", "who are you", "what is your name", "your name",
        "who developed you", "who developed", "who created you", "your creator", "contact details",
        "your mission", "your duty", "your duties", "your responsibility",
        "your responsibilities", "your capability", "your capabilities",
        "your strength", "your strengths", "what can you do",
    )

    def __init__(self, angel):
        self.angel = angel

    def can_answer(self, question):
        return _contains(question.lower(), self.KEYWORDS)

    def answer(self, question):
        return self.angel.greeting_reply(question)


class ApplicationActionEngine(AngelEngine):
    """Executes only navigation actions that are explicitly registered in FTMS."""

    name = "application_action"
    priority = 95
    COMMAND_PREFIX = re.compile(r"^\s*(?:open|go|navigate|add|create|edit|update|enter|manage)\b", re.I)

    def __init__(self, parent):
        self.actions = ActionRouter(parent)

    def can_answer(self, question):
        return bool(self.COMMAND_PREFIX.match(question)) and self.actions.matches(question)

    def answer(self, question):
        return self.actions.execute(question)


class DatabaseEngine(AngelEngine):
    name = "database"
    priority = 90

    def __init__(self, database_dna):
        self.database_dna = database_dna

    def can_answer(self, question):
        return self.database_dna.can_answer(question)

    def answer(self, question):
        return self.database_dna.answer(question)


class WritingEngine(AngelEngine):
    name = "writing"
    priority = 85
    COMMANDS = ("correct", "fix", "modify", "rewrite", "re-write", "re write", "improve", "proofread")

    def __init__(self, assistance):
        self.assistance = assistance

    def can_answer(self, question):
        text = question.lower().strip()
        return (
            self.assistance.answer(question) is not None
            or any(re.search(r"\b" + re.escape(command) + r"\b", text) for command in self.COMMANDS)
        )

    def answer(self, question):
        text = question.lower().strip()
        if any(re.search(r"\b" + re.escape(command) + r"\b", text) for command in self.COMMANDS):
            return self.assistance.rewrite_document(question)
        return self.assistance.answer(question)


class DateTimeEngineAdapter(AngelEngine):
    name = "date_time"
    priority = 80

    def __init__(self, date_time):
        self.date_time = date_time

    def can_answer(self, question):
        return self.date_time.can_answer(question)

    def answer(self, question):
        return self.date_time.answer(question)


class ComplianceAlertEngine(AngelEngine):
    """Provides actionable, database-first Mulkiya and insurance alerts."""

    name = "compliance_alert"
    priority = 87
    KEYWORDS = (
        "expiry", "expire", "expired", "expiring", "near expiry", "renewal",
        "mulkiya", "registration", "insurance", "compliance alert",
    )
    EXTERNAL_TERMS = ("rta", "rule", "rules", "regulation", "regulations", "fee", "fees", "office", "branch", "document")

    def __init__(self, compliance):
        self.compliance = compliance

    def can_answer(self, question):
        text = question.lower()
        if _contains(text, self.EXTERNAL_TERMS) or _contains(text, ("new vehicle", "new car", "new truck", "first registration")):
            return False
        topic = _contains(text, ("mulkiya", "registration", "insurance"))
        expiry_request = _contains(text, ("expiry", "expire", "expired", "expiring", "near expiry", "renewal", "alert"))
        return expiry_request and (topic or "expiry" in text or "expire" in text)

    def answer(self, question):
        text = question.lower()
        category = "insurance" if "insurance" in text else "registration" if any(
            term in text for term in ("mulkiya", "registration")
        ) else "all"
        alerts = self.compliance.expiry_alerts(category)
        if not alerts:
            label = {"insurance": "insurance", "registration": "Mulkiya registration", "all": "insurance or Mulkiya registration"}[category]
            return f"I checked FTMS and found no {label} records expiring within the next 30 days."

        red = [alert for alert in alerts if alert["severity"] == "RED"]
        amber = [alert for alert in alerts if alert["severity"] == "AMBER"]
        lines = ["I checked the FTMS compliance records."]
        if red:
            lines.append(f"\nRED ALERT - {len(red)} item(s) need immediate action:")
            lines.extend(self._format_alert(alert) for alert in red[:10])
        if amber:
            lines.append(f"\nAMBER ALERT - {len(amber)} item(s) are due within 30 days:")
            lines.extend(self._format_alert(alert) for alert in amber[:10])
        lines.append(
            "\nRecommended action: prioritise red items before dispatch, confirm renewal ownership and appointments, "
            "then update the FTMS record after renewal."
        )
        return "\n".join(lines)

    @staticmethod
    def _format_alert(alert):
        days = alert["days_remaining"]
        timing = f"expired {-days} day(s) ago" if days < 0 else (
            "expires today" if days == 0 else f"expires in {days} day(s)"
        )
        return f"- {alert['plate']} - {alert['document_type']} {timing} ({alert['expiry_date']:%d %b %Y})"


class ReportEngine(AngelEngine):
    name = "report"
    priority = 75
    KEYWORDS = (
        "report", "show", "list", "view", "under repair", "in repair",
        "expired insurance", "insurance due", "registration due", "open breakdown",
    )

    def __init__(self, intelligence):
        self.intelligence = intelligence

    def can_answer(self, question):
        return bool(re.match(r"^\s*(select|insert|update|delete|drop|alter|pragma)\b", question, re.I)) or _contains(
            question.lower(), self.KEYWORDS
        )

    def answer(self, question):
        return self.intelligence.report_answer(question)


class TechnicalEngine(AngelEngine):
    name = "technical"
    priority = 70
    KEYWORDS = (
        "chiller", "temperature", "overheating", "overheat", "battery", "tyre",
        "tire", "mechanical", "engine failure", "fault", "fuel leak",
    )

    def __init__(self, intelligence):
        self.intelligence = intelligence

    def can_answer(self, question):
        return _contains(question.lower(), self.KEYWORDS)

    def answer(self, question):
        return self.intelligence.technical_answer(question)


class FleetAnalysisEngine(AngelEngine):
    name = "fleet_analysis"
    priority = 65
    KEYWORDS = (
        "fleet", "vehicle", "vehicles", "driver", "drivers", "fuel", "maintenance",
        "odometer", "availability", "dispatch", "vehicle status", "driver performance",
    )

    def __init__(self, intelligence):
        self.intelligence = intelligence

    def can_answer(self, question):
        return _contains(question.lower(), self.KEYWORDS)

    def answer(self, question):
        return self.intelligence.fleet_answer(question)


class ProductKnowledgeEngine(AngelEngine):
    name = "product_knowledge"
    priority = 60

    def __init__(self):
        self.knowledge = FTMSKnowledge()

    def can_answer(self, question):
        return self.knowledge.detect_intent(question) is not None

    def answer(self, question):
        return self.knowledge.answer(question)


class RegulatoryEngine(AngelEngine):
    """Answers authority questions from approved websites, never FTMS records."""

    name = "regulatory"
    priority = 88
    KEYWORDS = (
        "rta", "roads and transport authority", "dubai police", "abu dhabi police",
        "traffic", "fine", "fines", "mohre", "labour", "labor", "uae rules",
        "uae regulations", "uae law", "government rules", "government regulations",
        "dubai rules", "dubai regulations", "abu dhabi rules", "abu dhabi regulations",
        "sharjah rules", "sharjah regulations", "ajman rules", "ajman regulations",
        "ras al khaimah rules", "ras al khaimah regulations", "fujairah rules",
        "fujairah regulations", "umm al quwain rules", "umm al quwain regulations",
        "mulkiya", "vehicle passing", "chiller passing", "vehicle chiller",
        "heavy truck", "heavy vehicle", "speed limit", "driving rules",
        "road crossing", "pedestrian crossing", "police rules",
    )
    RTA_DOMAINS = ("rta.ae", "evg.ae", "u.ae")
    DUBAI_TRAFFIC_DOMAINS = ("dubaipolice.gov.ae", "rta.ae", "u.ae")
    ABU_DHABI_TRAFFIC_DOMAINS = ("adpolice.gov.ae", "u.ae")
    SHARJAH_TRAFFIC_DOMAINS = ("srta.gov.ae", "sharjah.ae", "u.ae")
    FEDERAL_TRAFFIC_DOMAINS = ("moi.gov.ae", "u.ae")
    RTA_SERVICE_TERMS = (
        "mulkiya", "registration", "vehicle passing", "chiller", "heavy truck",
        "heavy vehicle", "timing", "fee", "document", "office", "branch",
        "traffic", "driving", "speed", "fine", "permit",
    )

    def __init__(self, lookup):
        self.lookup = lookup

    def can_answer(self, question):
        text = self._normalise_authority_name(question)
        return _contains(text, self.KEYWORDS) or (
            _contains(text, (
                "uae", "dubai", "abu dhabi", "sharjah", "ajman", "ras al khaimah",
                "fujairah", "umm al quwain", "government",
            ))
            and _contains(text, ("rule", "rules", "regulation", "regulations", "law", "laws", "permit", "permits"))
        )

    def answer(self, question):
        normalized_question = self._normalise_authority_name(question)
        if self.requires_clarification(normalized_question):
            return (
                "Sir, did you mean RTA rules and regulations? If so, I can bring the exact official details "
                "for your query. Please tell me whether you need Mulkiya renewal, vehicle or chiller passing, "
                "heavy-truck timings, traffic fines, speed limits, permits, fees, documents, or RTA office locations."
            )
        return self.lookup.answer(normalized_question, self._source_domains(normalized_question))

    @staticmethod
    def _normalise_authority_name(question):
        """Correct common authority-name typos before intent or source selection."""
        return re.sub(r"\brts\b", "rta", question.lower())

    def requires_clarification(self, question):
        text = self._normalise_authority_name(question)
        return (
            _contains(text, ("rta",))
            and _contains(text, ("new rule", "new rules", "latest rule", "latest rules", "current rule", "current rules"))
            and not _contains(text, self.RTA_SERVICE_TERMS)
        )

    def _source_domains(self, text):
        """Select the responsible official authority before running the lookup."""
        if _contains(text, ("rta", "mulkiya", "registration", "vehicle passing", "chiller", "heavy truck", "heavy vehicle")):
            return self.RTA_DOMAINS
        if _contains(text, ("dubai",)) and _contains(text, ("traffic", "driving", "speed", "road", "pedestrian", "police", "fine")):
            return self.DUBAI_TRAFFIC_DOMAINS
        if _contains(text, ("abu dhabi",)) and _contains(text, ("traffic", "driving", "speed", "road", "pedestrian", "police", "fine")):
            return self.ABU_DHABI_TRAFFIC_DOMAINS
        if _contains(text, ("sharjah",)) and _contains(text, ("traffic", "driving", "speed", "road", "pedestrian", "police", "fine")):
            return self.SHARJAH_TRAFFIC_DOMAINS
        if _contains(text, ("traffic", "driving", "speed", "road", "pedestrian", "police", "fine")):
            return self.FEDERAL_TRAFFIC_DOMAINS
        return ("u.ae", "gov.ae")


class ApprovedSourceFallbackEngine(AngelEngine):
    """Last-resort external lookup that exposes only authority-approved results."""

    name = "approved_source_fallback"
    priority = 0

    def __init__(self):
        self.lookup = ApprovedInternetLookup()

    def can_answer(self, question):
        return len(question.strip()) >= 3

    def answer(self, question):
        return self.lookup.answer(question)
