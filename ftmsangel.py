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
from .intent_router import IntentRouter
from .operations_engine import ApprovedInternetLookup
from .query_clarifier import QueryClarifier


class Angel:
    """Friendly, safe FTMS assistance backed by one modular intent router."""

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
            return "I am here to help. Please ask a fleet question, request a report, or give me a task."
        authority = self.conversation_context.consume_authority_confirmation(question)
        if authority:
            return (
                f"Certainly, Sir. Please tell me the exact {authority} service or rule you need, "
                "such as Mulkiya renewal, chiller passing, traffic fines, speed limits, documents, fees, or office locations."
            )
        corrected_question = self.conversation_context.consume_correction_confirmation(question)
        if corrected_question == "":
            return "No problem, Sir. Please rephrase your question and I will help you find the correct information."
        if corrected_question:
            question = corrected_question
        else:
            clarification = self.query_clarifier.suggest(question)
            if clarification:
                corrected_question, _substitutions = clarification
                self.conversation_context.set_pending_correction(corrected_question)
                return (
                    f'Sir, did you mean "{corrected_question}"? If so, I can check FTMS first or the relevant '
                    "official source and provide accurate details."
                )
        try:
            detected_intent = self.intent_router.detect(question)
            intent = self.conversation_context.resolve(question, detected_intent)
            answer = self.intent_router.route(question, intent)
        except Exception:
            return "I could not complete that request safely. Please try again or provide more detail."
        self.conversation_context.record(intent, answer)
        regulatory = self.intent_router.engine("regulatory")
        if intent == "regulatory" and regulatory and regulatory.requires_clarification(question):
            self.conversation_context.set_pending_authority("RTA")
        return answer or "I could not identify the right source for that request. Please provide more detail."

    def greeting_reply(self, question):
        """Handle greetings with EXACT echo-back - NO FTMS MENU."""
        text = re.sub(r"\s+", " ", question.lower()).strip()
        
        # Special knowledge questions
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
            return "Hi, How are you. How can I help you today?"
        if any(term in text for term in ("who are you", "what is your name", "your name")):
            return (
                "My name is Angel. I am your friendly FTMS FleetPro intelligent assistant, here to help you "
                "understand fleet operations, identify risks, and make confident decisions."
            )
        
        # TIME-BASED GREETINGS - EXACT ECHO-BACK
        if "good morning" in text:
            return "Good Morning. How can I help you today?"
        if "good afternoon" in text or "good after noon" in text:
            return "Good Afternoon. How can I help you today?"
        if "good evening" in text:
            return "Good Evening. How can I help you today?"
        if "good night" in text:
            return "Good Night. How can I help you today?"
        if text == "morning":
            return "Good Morning. How can I help you today?"
        if text == "afternoon" or text == "after noon":
            return "Good Afternoon. How can I help you today?"
        if text == "evening":
            return "Good Evening. How can I help you today?"
        if text == "night":
            return "Good Night. How can I help you today?"
        
        # BASIC GREETINGS - EXACT ECHO-BACK
        if any(term in text for term in ("hi", "hey", "hello", "hai", "hii", "helo", "hellow")):
            return "Hi. How can I help you today?"
        
        # Farewells
        if any(term in text for term in ("bye", "goodbye", "farewell", "see you", "take care")):
            return "Thank you. Have a great day!"
        
        # Default fallback
        return "Hello. How can I help you today?"
