"""ANGEL: the FleetPro decision-support assistant."""

import re

from .assistance_engine import AssistanceEngine
from .core_engines import (
    ApplicationActionEngine,
    ApprovedSourceFallbackEngine,
    ComplianceAlertEngine,
    ConversationEngine,
    DatabaseEngine,
    DateTimeEngineAdapter,
    FleetAnalysisEngine,
    ProductKnowledgeEngine,
    RegulatoryEngine,
    ReportEngine,
    TechnicalEngine,
    WritingEngine,
)
from .compliance_intelligence import ComplianceIntelligence
from .conversation_context import ConversationContext
from .database_dna import DatabaseDNA
from .DateTimeEngine import DateTimeEngine
from .engine_contract import AngelEngine
from .fleet_intelligence import FleetIntelligence
from .greeting_classifier import GreetingClassifier
from .intent_router import IntentRouter
from .operations_engine import ApprovedInternetLookup
from .query_clarifier import QueryClarifier


class Angel:
    """Friendly, safe FTMS assistance backed by one modular intent router."""

    DEAD_END_FALLBACKS = (
        "i could not locate",
        "i don't know",
        "no information found",
        "i could not identify the right source",
        "i could not reach an official authority source right now",
    )
    SUGGESTIONS_PROMPT = "Would you like suggestions regarding this topic?"

    def __init__(self, parent, db_path):
        self.parent = parent
        self.db_path = str(db_path)
        self.current_module = "Dashboard"
        self.current_filter = None
        self.awaiting_contact_details = False

        self.database_dna = DatabaseDNA(self.db_path)
        self.compliance = ComplianceIntelligence(self.db_path)
        self.intelligence = FleetIntelligence(self.db_path)
        self.assistance = AssistanceEngine()
        self.datetimes = DateTimeEngine()
        self.intent_router = IntentRouter(self._default_engines())
        self.conversation_context = ConversationContext()
        self.query_clarifier = QueryClarifier()
        self.greeting_classifier = GreetingClassifier()

    def _default_engines(self):
        regulatory_lookup = ApprovedInternetLookup()
        return (
            ConversationEngine(self),
            ApplicationActionEngine(self.parent),
            DatabaseEngine(self.database_dna),
            WritingEngine(self.assistance),
            ComplianceAlertEngine(self.compliance),
            DateTimeEngineAdapter(self.datetimes),
            ReportEngine(self.intelligence),
            TechnicalEngine(self.intelligence),
            FleetAnalysisEngine(self.intelligence),
            ProductKnowledgeEngine(),
            RegulatoryEngine(regulatory_lookup),
            ApprovedSourceFallbackEngine(),
        )

    def set_context(self, module, filter_value=None):
        self.current_module = module
        self.current_filter = filter_value

    def register_module_engine(self, name, engine, priority=60, matcher=None):
        """Register a future engine using the common ANGEL engine contract."""
        if matcher is not None:
            raise ValueError("Matchers are no longer supported; implement can_answer on the engine.")
        if not isinstance(engine, AngelEngine):
            raise TypeError("Module engines must inherit from AngelEngine.")
        engine.name = name
        engine.priority = priority
        self.intent_router.register(engine)

    def unregister_module_engine(self, name):
        self.intent_router.unregister(name)

    def available_module_engines(self):
        return self.intent_router.engine_names()

    def set_intent_detector(self, detector):
        """Inject a future LLM detector without changing engine implementations."""
        self.intent_router.set_detector(detector)

    def refresh_resources(self):
        """Reserved for database-backed engines that cache schema or metadata."""

    def reply(self, question):
        question = (question or "").strip()
        if not question:
            return self._finalize_response(
                "I am here to help. Please ask a fleet question, request a report, or give me a task."
            )
        authority = self.conversation_context.consume_authority_confirmation(question)
        if authority:
            return self._finalize_response(
                f"Certainly, Sir. Please tell me the exact {authority} service or rule you need, "
                "such as Mulkiya renewal, chiller passing, traffic fines, speed limits, documents, fees, or office locations."
            )
        corrected_question = self.conversation_context.consume_correction_confirmation(question)
        if corrected_question == "":
            return self._finalize_response(
                "No problem, Sir. Please rephrase your question and I will help you find the correct information."
            )
        if corrected_question:
            question = corrected_question
        else:
            greeting = self.greeting_classifier.classify(question)
            if greeting["class"] != "non_greeting":
                return self._finalize_response(self._greeting_response(question, greeting), greeting["class"])
            clarification = self.query_clarifier.suggest(question)
            if clarification:
                corrected_question, _substitutions = clarification
                self.conversation_context.set_pending_correction(corrected_question)
                return self._finalize_response(
                    f'Sir, did you mean "{corrected_question}"? If so, I can check FTMS first or the relevant '
                    "official source and provide accurate details."
                )
        try:
            intent, answer = self._route_question(question)
        except Exception:
            return self._finalize_response("I could not complete that request safely. Please try again or provide more detail.")
        regulatory = self.intent_router.engine("regulatory")
        if intent == "regulatory" and regulatory and regulatory.requires_clarification(question):
            self.conversation_context.set_pending_authority("RTA")
        return self._finalize_response(
            answer or "I could not identify the right source for that request. Please provide more detail.",
            intent,
        )

    def _route_question(self, question):
        detected_intent = self.intent_router.detect(question)
        intent = self.conversation_context.resolve(question, detected_intent)
        return intent, self.intent_router.route(question, intent)

    def _finalize_response(self, answer, intent=None):
        self.conversation_context.record(intent, answer)
        self.conversation_context.record_response(answer)
        return answer

    def _greeting_response(self, question, greeting):
        classification = greeting["class"]
        if classification == "greeting_plus_task":
            return self._greeting_plus_task_response(greeting)
        if classification == "wellbeing_query":
            return self._select_non_repetitive(
                (
                    "I’m doing well, thank you. How can I help you today?",
                    "Doing well, thank you. What would you like to check?",
                )
            )
        if classification == "time_greeting":
            template_key = greeting["response_template_key"]
            options = {
                "greeting.time.morning": (
                    "Good morning! How can I help you today?",
                    "Good morning! What would you like to check?",
                ),
                "greeting.time.afternoon": (
                    "Good afternoon! How may I assist you today?",
                    "Good afternoon! How can I help?",
                ),
                "greeting.time.evening": (
                    "Good evening! What would you like to check?",
                    "Good evening! How may I assist you today?",
                ),
            }
            return self._select_non_repetitive(options.get(template_key, ("Hello! How can I help you today?",)))
        if classification == "basic_greeting":
            return self._select_non_repetitive(
                (
                    "Hi! How can I help you today?",
                    "Hello! What can I do for you?",
                    "Hey! How may I assist?",
                )
            )
        if classification == "farewell":
            return self._select_non_repetitive(
                (
                    "Thank you. Have a great day!",
                    "Okay. Thank you. All the best.",
                )
            )
        return self.greeting_reply(question)

    def _greeting_plus_task_response(self, greeting):
        task_question = greeting.get("task_text") or greeting["normalized_text"]
        try:
            _task_intent, task_answer = self._route_question(task_question)
        except Exception:
            task_answer = None
        if self._contains_dead_end(task_answer):
            rescued_answer = self.assistance.answer(task_question)
            task_answer = rescued_answer or self._safe_task_clarifier(greeting)
        prefix = self._task_greeting_prefix(greeting)
        task_answer = self._ensure_suggestions_prompt(task_answer)
        if greeting["threshold_band"] == "medium":
            task_answer = f"If you mean this request, {task_answer[:1].lower()}{task_answer[1:]}"
        return f"{prefix} {task_answer}".strip()

    def _task_greeting_prefix(self, greeting):
        token = greeting["detected_greeting_tokens"][0] if greeting["detected_greeting_tokens"] else "hello"
        if token == "morning":
            return "Good morning!"
        if token == "afternoon":
            return "Good afternoon!"
        if token == "evening":
            return "Good evening!"
        return "Hi!"

    def _safe_task_clarifier(self, greeting):
        task_tokens = greeting.get("detected_task_tokens") or []
        if any(token in task_tokens for token in ("documents", "requirements", "renewal", "mulkiya", "registration", "chiller", "passing", "permit")):
            return "Please tell me the exact service or document type you need, and I will help right away."
        return "Please tell me the exact topic you need, and I will help right away."

    def _ensure_suggestions_prompt(self, answer):
        answer = (answer or "").strip()
        if self.SUGGESTIONS_PROMPT in answer:
            return answer
        return f"{answer}\n\n{self.SUGGESTIONS_PROMPT}" if answer else self.SUGGESTIONS_PROMPT

    def _contains_dead_end(self, answer):
        lowered = (answer or "").lower()
        return not answer or any(phrase in lowered for phrase in self.DEAD_END_FALLBACKS)

    def _select_non_repetitive(self, options):
        recent = set(self.conversation_context.recent_assistant_turns())
        for option in options:
            if len(option.split()) > 6 and option in recent:
                continue
            return option
        return options[0]

    def greeting_reply(self, question):
        text = re.sub(r"\s+", " ", question.lower()).strip()
        if any(term in text for term in ("who developed you", "who developed", "who created you", "your creator")):
            return (
                "I was developed by Thankappan Dharmanathan for FTMS FleetPro. "
                "My purpose is to support safer, faster, and better-informed fleet decisions."
            )
        if any(term in text for term in ("your mission", "your duty", "your duties")):
            return (
                "My mission is to be a friendly and reliable FleetPro decision-support assistant. "
                "I check FTMS data first, identify operational and compliance risks, explain what they mean, "
                "and guide you toward the right next action."
            )
        if any(term in text for term in ("your responsibility", "your responsibilities")):
            return (
                "My responsibilities are to answer fleet questions clearly, review authorised FTMS records, "
                "highlight expiry and operational risks, prepare safe reports and professional documents, "
                "and use official authority sources when FleetPro has no relevant answer."
            )
        if any(term in text for term in ("your capability", "your capabilities", "what can you do")):
            return (
                "I can help with fleet status, vehicle and driver readiness, fuel and technical guidance, "
                "Mulkiya and insurance expiry alerts, safe FTMS reports, database structure questions, "
                "professional sentence correction, warning-letter drafts, approved application navigation, "
                "and current official UAE authority guidance."
            )
        if any(term in text for term in ("your strength", "your strengths")):
            return (
                "My strengths are structured decision support, database-first answers, safe read-only reporting, "
                "clear red and amber compliance alerts, practical operational guidance, and official-source "
                "verification when an answer is outside FleetPro."
            )
        if "how are you" in text:
            return "I am well and ready to help. What would you like to check in FTMS FleetPro?"
        if any(term in text for term in ("who are you", "what is your name", "your name")):
            return (
                "My name is Angel. I am your friendly FTMS FleetPro intelligent assistant, here to help you "
                "understand fleet operations, identify risks, and make confident decisions."
            )
        return "Hello. I am Angel, your FTMS FleetPro assistant. How can I help you today?"
