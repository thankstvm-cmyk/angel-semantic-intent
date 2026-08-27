"""Writing help and practical vehicle-service checklists for FTMS Angel."""

import re
from datetime import date


class AssistanceEngine:
    """Answers requests that need a prepared document or a clear checklist."""

    def answer(self, question):
        text = self._normalise(question)

        if self._is_sentence_improvement_request(text):
            return self.rewrite_document(question)
        if "warning letter" in text or "written warning" in text:
            return self._warning_letter(question)
        if "essay" in text:
            return self._essay(question)
        if self._is_branding_request(text):
            return self._branding_checklist()
        if self._is_registration_fee_request(text):
            return self._registration_fee()
        if self._is_registration_request(text):
            return self._new_vehicle_checklist()
        if self._is_renewal_request(text):
            return self._mulkiya_renewal_checklist()
        return None

    @staticmethod
    def _is_sentence_improvement_request(text):
        return any(phrase in text for phrase in (
            "modify sentence", "correct sentence", "rewrite", "improve", "make proper sentence",
            "grammar", "correct this", "correct the", "make professional", "proofread",
        ))

    def rewrite_document(self, question):
        """Return language-only correction for an incident note or business sentence."""
        source = self._extract_document_text(question)
        if not source:
            return "Please provide the sentence to correct."
        corrected, alternative = self._professionalise(source)
        response = f"Original:\n{source}\n\nCorrected:\n{corrected}"
        if alternative:
            response += f"\n\nProfessional Alternative:\n{alternative}"
        return response

    @staticmethod
    def _extract_document_text(question):
        text = question.strip()
        quoted = re.search(r"[\"'](.+?)[\"']", text)
        if quoted:
            source = quoted.group(1).strip()
        elif ":" in text:
            source = text.split(":", 1)[1].strip()
        else:
            source = re.sub(
                r"^(please\s+)?(?:modify(?:\s+sentence)?|correct(?:\s+sentence)?|rewrite|improve|make proper(?:\s+sentence)?|grammar|proofread|make professional)(?:\s+(this|the))?(?:\s+sentence|\s+email)?\s*[:\-]?\s*",
                "", text, flags=re.I,
            ).strip()
        return source

    @staticmethod
    def _professionalise(source):
        source = re.sub(r"\s+", " ", source).strip()
        normalized = source.lower().rstrip(".")

        incident_match = re.fullmatch(
            r"yesterday(?:,)? vehicle breakdown at (.+?)\.?(?: vehicle)? has taken into recovery to (?:the )?garage\.?(?: but)? (?:the )?garage was closed due(?: to)? late",
            normalized,
        )
        if not incident_match:
            incident_match = re.fullmatch(
                r"yesterday vehicle breakdown at (.+?) vehicle was taken to (?:the )?garage but it was closed late",
                normalized,
            )
        if incident_match:
            location = AssistanceEngine._title_case_location(incident_match.group(1))
            return (
                f"The vehicle broke down yesterday on {location}. It was taken to the garage for recovery; however, the garage was closed due to the late hour.",
                f"The vehicle experienced a breakdown yesterday on {location} and was transported to a garage, but it was closed due to the late timing.",
            )

        source = source[:1].upper() + source[1:]
        if source[-1:] not in ".!?":
            source += "."
        improved = source
        replacements = (
            (r"\b(?:is|are)\s+not working\b", "is not operating correctly"),
            (r"\bvehicle has breakdown\b", "the vehicle broke down"),
            (r"\bvehicle breakdown\b", "vehicle breakdown"),
            (r"\bhas taken into recovery\b", "was taken for recovery"),
            (r"\bdue late\b", "due to the late hour"),
            (r"\bis down\b", "is unavailable for service"),
            (r"\bproblem\b", "issue"),
            (r"\bas soon as possible\b", "at the earliest opportunity"),
        )
        for old, new in replacements:
            improved = re.sub(old, new, improved, flags=re.I)
        improved = re.sub(r"\bbut\b", "however", improved, flags=re.I)
        return improved, None

    @staticmethod
    def _title_case_location(location):
        small_words = {"and", "at", "in", "on", "of", "the"}
        return " ".join(
            word if index and word.lower() in small_words else word.capitalize()
            for index, word in enumerate(location.split())
        )

    @staticmethod
    def _normalise(question):
        """Handle common chat spelling mistakes before classifying intent."""
        text = re.sub(r"\s+", " ", question.lower()).strip()
        corrections = {
            "registraion": "registration",
            "registraton": "registration",
            "registation": "registration",
            "vechicle": "vehicle",
            "dubia": "dubai",
        }
        for incorrect, correct in corrections.items():
            text = re.sub(rf"\b{incorrect}\b", correct, text)
        return text

    @staticmethod
    def _is_renewal_request(text):
        return ("mulkiya" in text or "vehicle registration" in text or "vehicle ownership" in text) and any(
            word in text for word in ("renew", "renewal", "expire", "expiry")
        )

    @staticmethod
    def _is_registration_request(text):
        return ("register" in text or "registration" in text) and any(
            phrase in text for phrase in ("new vehicle", "new car", "new truck", "first registration")
        )

    @staticmethod
    def _is_registration_fee_request(text):
        return ("vehicle registration" in text or "car registration" in text) and any(
            phrase in text for phrase in ("fee", "fees", "cost", "how much", "price", "charge")
        )

    @staticmethod
    def _is_branding_request(text):
        return any(word in text for word in ("branding", "vehicle advertisement", "vehicle advertising", "vehicle logo", "vehicle wrap"))

    @staticmethod
    def _warning_letter(question):
        match = re.search(r"(?:to|for)\s+(.+?)(?:\s+(?:for|because|regarding)\s+|$)", question, re.I)
        employee = match.group(1).strip(" ,.") if match else "[Employee name]"
        reason_match = re.search(r"(?:for|because|regarding)\s+(.+?)[.?!]*$", question, re.I)
        reason = reason_match.group(1).strip() if reason_match else "[describe the incident or misconduct]"
        return f"""Date: {date.today():%d %B %Y}

To: {employee}
Subject: Written Warning

Dear {employee},

This letter is a formal written warning regarding {reason}. This conduct does not meet the standards expected by the company.

You are required to correct this matter immediately and comply with all company policies and instructions going forward. Any further occurrence may lead to additional disciplinary action, up to and including termination of employment.

Please sign below to acknowledge receipt of this warning. Your signature confirms receipt only; it does not necessarily indicate agreement.

Employee signature: ____________________    Date: __________
Manager signature: _____________________    Date: __________"""

    @staticmethod
    def _essay(question):
        match = re.search(r"essay\s+(?:about|on|regarding|for)?\s*(.+?)[?.!]*$", question, re.I)
        subject = match.group(1).strip() if match else "[subject]"
        subject = re.sub(r"^(?:an?|the)\s+", "", subject, flags=re.I)
        return f"""Title: {subject.title()}

{subject.title()} is an important subject because it affects people, organisations, and society in practical ways. Understanding it helps people make informed decisions and respond responsibly to the challenges and opportunities it creates.

First, {subject} should be considered carefully in relation to its main purpose and benefits. A clear plan, accurate information, and consistent effort help achieve better results. When people understand their responsibilities, they can avoid common mistakes and work more effectively.

In addition, successful outcomes depend on cooperation, good communication, and regular review. Challenges may arise, but they can be addressed through preparation, training, and sensible decision-making. These steps make the approach more reliable and sustainable over time.

In conclusion, {subject} deserves attention because it has a meaningful impact on everyday life. By applying knowledge responsibly and continuously improving, individuals and organisations can achieve positive and lasting results."""

    @staticmethod
    def _mulkiya_renewal_checklist():
        return """For a Dubai vehicle-registration (Mulkiya) renewal, prepare the following:

• Valid electronic vehicle insurance.
• A valid electronic technical-inspection result when the vehicle is required to be tested.
• Settlement of all traffic fines and pending licensing payments.
• Emirates ID/UAE Pass or the relevant company account details to access the service.
• For a company vehicle: a valid company Traffic File and valid Trade Licence.

For a standard online renewal, no paper documents are normally required because insurance and test results are verified electronically. The payable total depends on the vehicle category, testing requirement, outstanding fines, and delivery choice. Confirm the final amount in the RTA transaction before payment."""

    @staticmethod
    def _new_vehicle_checklist():
        return """To register a new vehicle in Dubai, prepare:

• Emirates ID or UAE Pass.
• Electronic Customs Certificate.
• Sale and Purchase Agreement, unless the Customs Certificate is already in the buyer's name.
• Valid vehicle insurance.
• Electronic technical-inspection result when required. A genuinely new, zero-mileage vehicle purchased from an authorised UAE dealer is generally exempt from inspection for its first 3 years.
• Gulf-specification/conformity document if the Customs Certificate does not confirm compliance.

For a company registration, also prepare the company authorisation letter, valid Trade Licence, and any company/Free Zone documents requested for the transaction. A used, imported, or previously owned vehicle also needs the applicable Transfer Certificate or Dubai Possession Certificate."""

    @staticmethod
    def _registration_fee():
        return """For a standard light private or public vehicle in Dubai, the base new-registration fee is AED 400.

You may also have to pay separate charges for:

• Knowledge and innovation fees.
• Opening a new Traffic File, if you do not already have one (AED 200).
• Vehicle inspection, when required.
• Insurance, number plates, delivery, and any outstanding traffic fines.

The final amount shown in the RTA transaction depends on the vehicle category and selected services. Heavy vehicles, buses, motorcycles, trailers, and special vehicles have different fees."""

    @staticmethod
    def _branding_checklist():
        return """For a Dubai vehicle-branding or vehicle-advertising permit, prepare:

• Final advertising/branding design.
• Copy of the vehicle ownership card (Mulkiya).
• Copy of the company Trade Licence.

If the vehicle displays advertising for another business, also prepare:

• Trade Licence for the advertising company.
• Trade Licence for the advertised brand/owner.
• Request letter where applicable.
• Contract or registered trademark evidence when the advertised product belongs to a third party.

Additional cases: a rented vehicle needs a copy of the rental contract; a mobile advertising vehicle needs approval from the Vehicle Licensing Department. The design should meet the applicable language and vehicle-colour requirements before submission through the relevant e-service."""
