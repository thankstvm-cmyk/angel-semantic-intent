"""Live operational intelligence and safe application actions for FTMS Angel.

This module is intentionally read-only for questions.  User-facing actions are
limited to opening existing FTMS screens registered in ``ActionRouter``.
"""

import re
import sqlite3
from html import unescape
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta


class FleetOperationsEngine:
    def __init__(self, db_path):
        self.db_path = str(db_path)
        self._schema = None

    def available_resources(self):
        """Return the live database resources Angel can safely use."""
        if self._schema is None:
            try:
                with sqlite3.connect(self.db_path) as connection:
                    tables = [row[0] for row in connection.execute(
                        "SELECT name FROM sqlite_master WHERE type = 'table'"
                    )]
                    self._schema = {
                        table: {row[1] for row in connection.execute(
                            'PRAGMA table_info("{}")'.format(table.replace('"', '""'))
                        )}
                        for table in tables
                    }
            except sqlite3.Error:
                self._schema = {}
        return self._schema

    def _has_columns(self, table, *columns):
        return set(columns).issubset(self.available_resources().get(table, set()))

    def _query(self, sql, parameters=()):
        try:
            with sqlite3.connect(self.db_path) as connection:
                return connection.execute(sql, parameters).fetchall()
        except sqlite3.Error:
            return []

    def _plates(self, rows):
        plates = ["-".join(str(value) for value in row if value not in (None, "")) for row in rows]
        return ", ".join(plates[:10]) + (" …" if len(plates) > 10 else "")

    def answer(self, question):
        """Answer known operational questions from FTMS first; return None otherwise."""
        text = re.sub(r"\s+", " ", question.lower()).strip()
        today = date.today().isoformat()
        end_30 = (date.today() + timedelta(days=30)).isoformat()

        if ("under repair" in text or "in repair" in text) and self._has_columns("vehicles", "plate_source", "plate_code", "plate_number", "status") and any(word in text for word in ("vehicle", "truck", "fleet", "which", "show")):
            rows = self._query("""SELECT plate_source, plate_code, plate_number FROM vehicles
                                WHERE LOWER(COALESCE(status, '')) LIKE '%repair%' ORDER BY plate_number""")
            return self._vehicle_answer(rows, "under repair")

        if ("expired insurance" in text or ("insurance" in text and "expired" in text)) and self._has_columns("vehicle_insurance", "vehicle_id", "expiry_date") and self._has_columns("vehicles", "id", "plate_source", "plate_code", "plate_number"):
            rows = self._query("""SELECT v.plate_source, v.plate_code, v.plate_number, i.expiry_date
                                FROM vehicle_insurance i JOIN vehicles v ON v.id = i.vehicle_id
                                WHERE DATE(i.expiry_date) < DATE(?) ORDER BY i.expiry_date""", (today,))
            if not rows:
                return "FTMS database: no expired insurance policies were found."
            items = ", ".join(f"{self._plates([row[:3]])} ({row[3]})" for row in rows[:10])
            return f"FTMS database: {len(rows)} vehicle(s) have expired insurance: {items}."

        if "insurance" in text and any(word in text for word in ("due", "expiring", "expire", "next 30", "renewal")) and self._has_columns("vehicle_insurance", "vehicle_id", "expiry_date") and self._has_columns("vehicles", "id", "plate_source", "plate_code", "plate_number"):
            rows = self._query("""SELECT v.plate_source, v.plate_code, v.plate_number, i.expiry_date
                                FROM vehicle_insurance i JOIN vehicles v ON v.id = i.vehicle_id
                                WHERE DATE(i.expiry_date) BETWEEN DATE(?) AND DATE(?) ORDER BY i.expiry_date""", (today, end_30))
            return f"FTMS database: {len(rows)} insurance policy/policies are due in the next 30 days." + (f" Vehicles: {self._plates([row[:3] for row in rows])}." if rows else "")

        if any(term in text for term in ("expired registration", "expired mulkiya", "registration expired")) and self._has_columns("vehicles", "plate_source", "plate_code", "plate_number", "mulkiya_expiry_date"):
            rows = self._query("""SELECT plate_source, plate_code, plate_number FROM vehicles
                                WHERE DATE(mulkiya_expiry_date) < DATE(?) ORDER BY mulkiya_expiry_date""", (today,))
            return self._vehicle_answer(rows, "with expired registration")

        if any(term in text for term in ("fleet status", "fleet summary", "how many vehicles", "total vehicles", "fleet availability")) and self._has_columns("vehicles", "status"):
            total = self._query("SELECT COUNT(*) FROM vehicles")[0][0]
            active = self._query("SELECT COUNT(*) FROM vehicles WHERE LOWER(COALESCE(status, '')) = 'active'")[0][0]
            repair = self._query("SELECT COUNT(*) FROM vehicles WHERE LOWER(COALESCE(status, '')) LIKE '%repair%'")[0][0]
            availability = round(active / total * 100, 1) if total else 0
            return f"FTMS database: {total} registered vehicles; {active} active ({availability}% availability) and {repair} under repair."

        if any(term in text for term in ("fuel cost", "fuel spending", "fuel expense")) and self._has_columns("fuel_entries", "total_cost", "date"):
            cost = self._query("SELECT COALESCE(SUM(total_cost), 0) FROM fuel_entries WHERE DATE(date) >= DATE(?)", ((date.today() - timedelta(days=30)).isoformat(),))[0][0]
            return f"FTMS database: fuel spending recorded in the last 30 days is {float(cost):,.2f}."

        if any(term in text for term in ("maintenance cost", "repair cost", "profitability", "profit", "cost control")):
            if not (self._has_columns("repairs", "cost", "repair_date") and
                    self._has_columns("breakdowns", "repair_cost", "breakdown_date") and
                    self._has_columns("fuel_entries", "total_cost", "date")):
                return None
            repair_cost = self._query("SELECT COALESCE(SUM(cost), 0) FROM repairs WHERE DATE(repair_date) >= DATE(?)", ((date.today() - timedelta(days=30)).isoformat(),))[0][0]
            breakdown_cost = self._query("SELECT COALESCE(SUM(repair_cost), 0) FROM breakdowns WHERE DATE(breakdown_date) >= DATE(?)", ((date.today() - timedelta(days=30)).isoformat(),))[0][0]
            fuel_cost = self._query("SELECT COALESCE(SUM(total_cost), 0) FROM fuel_entries WHERE DATE(date) >= DATE(?)", ((date.today() - timedelta(days=30)).isoformat(),))[0][0]
            total = float(repair_cost) + float(breakdown_cost) + float(fuel_cost)
            return (f"FTMS database: last-30-day recorded operating cost is {total:,.2f} "
                    f"(fuel {float(fuel_cost):,.2f}, repairs {float(repair_cost):,.2f}, breakdowns {float(breakdown_cost):,.2f}). "
                    "Profit cannot be calculated until revenue or trip-income data is recorded.")
        return None

    def business_insights(self):
        """Turn available FTMS data into practical, profit-protecting actions."""
        if not self._has_columns("vehicles", "status"):
            return None

        total = self._query("SELECT COUNT(*) FROM vehicles")
        active = self._query("SELECT COUNT(*) FROM vehicles WHERE LOWER(COALESCE(status, '')) = 'active'")
        repair = self._query("SELECT COUNT(*) FROM vehicles WHERE LOWER(COALESCE(status, '')) LIKE '%repair%'")
        if not total or not active or not repair:
            return None

        total_count, active_count, repair_count = total[0][0], active[0][0], repair[0][0]
        lines = [
            "Business improvement actions based on the current FTMS data:",
            f"• Fleet availability is {round(active_count / total_count * 100, 1) if total_count else 0}% ({active_count} of {total_count} active).",
        ]
        if repair_count:
            lines.append(f"• Prioritise the {repair_count} vehicle(s) under repair; returning them to service is the fastest way to protect utilisation and revenue.")
        else:
            lines.append("• No vehicles are currently marked under repair; maintain this position with preventive servicing.")

        if self._has_columns("fuel_entries", "vehicle_id", "total_cost", "date") and self._has_columns("vehicles", "id", "plate_number"):
            rows = self._query("""SELECT v.plate_number, SUM(f.total_cost) AS cost
                                  FROM fuel_entries f JOIN vehicles v ON v.id = f.vehicle_id
                                  WHERE DATE(f.date) >= DATE(?)
                                  GROUP BY v.id ORDER BY cost DESC LIMIT 1""",
                               ((date.today() - timedelta(days=30)).isoformat(),))
            if rows and rows[0][0] is not None:
                lines.append(f"• Review fuel use for vehicle {rows[0][0]} first: it has the highest recorded fuel spend in the last 30 days ({float(rows[0][1]):,.2f}).")

        if self._has_columns("vehicle_insurance", "expiry_date"):
            upcoming = self._query("SELECT COUNT(*) FROM vehicle_insurance WHERE DATE(expiry_date) BETWEEN DATE(?) AND DATE(?)",
                                   (date.today().isoformat(), (date.today() + timedelta(days=30)).isoformat()))
            if upcoming and upcoming[0][0]:
                lines.append(f"• Renew {upcoming[0][0]} insurance policy/policies due within 30 days to avoid disruption and last-minute costs.")
        lines.append("• Record trip revenue or income in FTMS to enable a true profit-per-vehicle calculation.")
        return "\n".join(lines)

    def _vehicle_answer(self, rows, description):
        if not rows:
            return f"FTMS database: no vehicles are {description}."
        return f"FTMS database: {len(rows)} vehicle(s) are {description}: {self._plates(rows)}."


class ActionRouter:
    """Registry-based navigation for current and future FTMS modules."""

    def __init__(self, parent):
        self.parent = parent
        self.actions = {}
        self.register_defaults()

    def application(self):
        try:
            return getattr(self.parent.winfo_toplevel(), "ftms_app", None)
        except Exception:
            return None

    def register(self, name, patterns, handler_name, confirmation):
        self.actions[name] = {"patterns": patterns, "handler": handler_name, "confirmation": confirmation}

    def register_defaults(self):
        self.register("add_vehicle", ("add vehicle", "new vehicle", "create vehicle", "register vehicle"), "open_add_vehicle", "Opening Add New Vehicle.")
        self.register("edit_vehicle", ("edit vehicle", "update vehicle", "change vehicle"), "open_logintoedit", "Opening Edit Vehicle Details.")
        self.register("insurance", ("add insurance", "insurance details", "insurance module", "renew insurance"), "open_vehicleins_page", "Opening Insurance Details.")
        self.register("vehicle_report", ("vehicle report", "fleet report", "show vehicles", "view vehicles"), "open_vehicle_report", "Opening Vehicle Report.")
        self.register("dashboard", ("open dashboard", "go dashboard", "show dashboard", "main dashboard"), "show_dashboard", "Opening Dashboard.")
        self.register("drivers", ("driver management", "manage drivers", "open drivers", "add driver"), "show_driver", "Opening Driver Management.")
        self.register("vehicle_management", ("vehicle management", "fuel management", "manage fuel"), "show_fuel", "Opening Vehicle Management.")
        self.register("odometer", ("odometer", "mileage entry", "enter mileage"), "show_odometer", "Opening Odometer Section.")
        self.register("reports", ("open reports", "report menu", "reports menu"), "show_reports", "Opening Report Section.")

    def execute(self, question):
        text = re.sub(r"\s+", " ", question.lower()).strip()
        app = self.application()
        for action in self.actions.values():
            if any(pattern in text for pattern in action["patterns"]):
                if app is None or not hasattr(app, action["handler"]):
                    return "I understood the requested module, but application navigation is not available in this window."
                getattr(app, action["handler"])()
                return action["confirmation"]
        return None

    def matches(self, question):
        """Return whether a registered action owns the request without executing it."""
        text = re.sub(r"\s+", " ", question.lower()).strip()
        return any(any(pattern in text for pattern in action["patterns"]) for action in self.actions.values())


class ApprovedInternetLookup:
    """Live public-information lookup restricted to official UAE sources.

    Regulations are never stored as hard-coded responses. Only the user's
    question is sent to search, and a result is used only after its source URL
    has passed official-domain validation.
    """

    APPROVED_DOMAINS = (
        "gov.ae",
        "u.ae",
        "rta.ae",
        "evg.ae",
        "sharjah.ae",
        "ajman.ae",
        "rak.ae",
        "fujairah.ae",
    )
    CACHE_TTL = timedelta(minutes=15)

    def __init__(self):
        self._cache = {}

    @staticmethod
    def _clean(text):
        text = re.sub(r"<[^>]+>", " ", text or "")
        return re.sub(r"\s+", " ", unescape(text)).strip()

    def _approved_url(self, url, allowed_domains=None):
        host = urllib.parse.urlparse(url).netloc.lower().split(":")[0]
        domains = allowed_domains or self.APPROVED_DOMAINS
        return any(host == domain or host.endswith("." + domain) for domain in domains)

    def _search(self, question, source_domains):
        sites = " OR ".join(f"site:{domain}" for domain in source_domains)
        query = urllib.parse.quote(f"{sites} {question} current official regulation")
        request = urllib.request.Request(
            "https://www.bing.com/search?format=rss&q=" + query,
            headers={"User-Agent": "FTMS-FleetPro-Angel/1.0"},
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.read()

    def _result_from_feed(self, feed, source_domains):
        root = ET.fromstring(feed)
        for item in root.findall(".//item"):
            title = self._clean(item.findtext("title"))
            link = (item.findtext("link") or "").strip()
            description = self._clean(item.findtext("description"))
            if link and description and self._approved_url(link, source_domains):
                return title, description, link
        return None

    def answer(self, question, preferred_domains=()):
        """Search a validated authority domain set and format its current result."""
        normalized = re.sub(r"\s+", " ", question.lower()).strip()
        if len(normalized) < 3:
            return None
        source_domains = tuple(preferred_domains) or self.APPROVED_DOMAINS
        if not all(self._approved_url(f"https://{domain}") for domain in source_domains):
            raise ValueError("Authority lookup received an unapproved source domain.")
        cache_key = (normalized, source_domains)
        cached = self._cache.get(cache_key)
        if cached and datetime.now() - cached["retrieved_at"] < self.CACHE_TTL:
            return cached["answer"]
        try:
            result = self._result_from_feed(self._search(question, source_domains), source_domains)
            if result:
                title, description, link = result
                answer = (
                    f"I checked the relevant official authority source.\n\nOfficial guidance — {title}\n\n{description}\n\n"
                    f"Official source: {link}\n"
                    f"Retrieved: {datetime.now():%d %b %Y, %I:%M %p}\n\n"
                    "Please confirm the final requirement or fee in the official service before submitting an application."
                )
            else:
                answer = (
                    "I could not locate a specific official page for that service. "
                    "Please provide the exact authority service, emirate, and vehicle or document type so I can refine the lookup."
                )
        except (OSError, urllib.error.URLError, ET.ParseError):
            answer = (
                "I could not reach an official authority source right now. "
                "Please try again shortly or specify the authority and emirate."
            )
        self._cache[cache_key] = {"answer": answer, "retrieved_at": datetime.now()}
        return answer


class WebAnswerLookup:
    """Use broad public web knowledge after the FTMS resources cannot answer.

    The answer is kept conversational: Angel does not show source-routing
    details to the user.  Only the user's question is searched; no database
    records are transmitted.
    """

    def __init__(self):
        self._cache = {}

    @staticmethod
    def _clean(text):
        text = re.sub(r"<[^>]+>", " ", text or "")
        return re.sub(r"\s+", " ", unescape(text)).strip()

    def _search(self, question):
        text = question.lower()
        # Authority-specific questions need an authority-specific answer. A
        # generic result can otherwise come from an unrelated news portal or
        # even a different country's transport system.
        if "rta" in text or "dubai vehicle" in text or "mulkiya" in text:
            question = "site:rta.ae " + question
        request = urllib.request.Request(
            "https://www.bing.com/search?format=rss&mkt=en-US&q=" + urllib.parse.quote(question),
            headers={"User-Agent": "FTMS-FleetPro-Angel/1.0"},
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.read()

    def _answer_from_feed(self, feed):
        root = ET.fromstring(feed)
        for item in root.findall(".//item"):
            title = self._clean(item.findtext("title"))
            link = (item.findtext("link") or "").strip()
            description = self._clean(item.findtext("description"))
            host = urllib.parse.urlparse(link).netloc.lower().split(":")[0]
            if (title and description and self._is_english(description)
                    and self._is_relevant_result(title, description, host)
                    and urllib.parse.urlparse(link).scheme in {"http", "https"}):
                # Keep the answer helpful without showing the site, URL, or
                # search-provider mechanics to the user.
                return description
        return None

    @staticmethod
    def _is_relevant_result(title, description, host):
        """Discard search/news landing pages instead of presenting them as answers."""
        combined = f"{title} {description}".lower()
        blocked = (
            "google news", "comprehensive up-to-date news coverage",
            "aggregated from sources", "lasg platedetect", "traffic analytics",
        )
        if any(phrase in combined for phrase in blocked):
            return False
        if "rta" in combined and host and not (host == "rta.ae" or host.endswith(".rta.ae")):
            return False
        return True

    @staticmethod
    def _is_english(text):
        """Reject non-English search snippets before they reach the chat."""
        if any(character.isalpha() and ord(character) > 127 for character in text):
            return False
        words = re.findall(r"[a-z]+", text.lower())
        if not words:
            return False
        english_markers = {"the", "and", "is", "are", "for", "with", "of", "to", "in", "a", "an"}
        return bool(set(words) & english_markers)

    def answer(self, question):
        normalized = re.sub(r"\s+", " ", question.lower()).strip()
        if len(normalized) < 3:
            return None
        if normalized not in self._cache:
            try:
                self._cache[normalized] = self._answer_from_feed(self._search(question))
            except Exception:
                self._cache[normalized] = None
        return self._cache[normalized] or (
            "I do not have a reliable answer for that yet. Please rephrase the question "
            "with a little more detail or try again shortly."
        )
