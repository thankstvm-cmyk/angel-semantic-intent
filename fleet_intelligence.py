"""Safe fleet, technical, and report intelligence for Angel."""

import re
import sqlite3
from datetime import date, timedelta


class FleetIntelligence:
    """Uses predefined, parameterized queries against the active FTMS data."""

    def __init__(self, db_path):
        self.db_path = str(db_path)

    def _query(self, sql, parameters=()):
        try:
            with sqlite3.connect(self.db_path) as connection:
                return connection.execute(sql, parameters).fetchall()
        except sqlite3.Error:
            return []

    def _count(self, sql, parameters=()):
        rows = self._query(sql, parameters)
        return rows[0][0] if rows else 0

    @staticmethod
    def _structured(analysis, causes, recommendation):
        return (
            f"🔍 Analysis:\n{analysis}\n\n"
            f"⚠️ Possible Causes:\n{causes}\n\n"
            f"✅ Recommendation:\n{recommendation}"
        )

    def fleet_answer(self, question):
        text = question.lower()
        total = self._count("SELECT COUNT(*) FROM vehicles")
        active = self._count("SELECT COUNT(*) FROM vehicles WHERE LOWER(COALESCE(status, '')) = 'active'")
        repair = self._count("SELECT COUNT(*) FROM vehicles WHERE LOWER(COALESCE(status, '')) LIKE '%repair%'")

        if any(term in text for term in ("fleet status", "fleet summary", "availability", "how many vehicle", "total vehicle")):
            availability = round(active / total * 100, 1) if total else 0
            return self._structured(
                f"The active fleet has {total} registered vehicles: {active} active and {repair} under repair. Availability is {availability}%.",
                "Vehicles marked under repair reduce dispatch capacity; missing or outdated statuses can also distort availability.",
                "Confirm repair release dates, assign replacement capacity before dispatch, and update vehicle status immediately after each operational change.",
            )
        if "fuel" in text:
            spend = self._count("SELECT COALESCE(SUM(total_cost), 0) FROM fuel_entries WHERE DATE(date) >= DATE(?)", ((date.today() - timedelta(days=30)).isoformat(),))
            entries = self._count("SELECT COUNT(*) FROM fuel_entries WHERE DATE(date) >= DATE(?)", ((date.today() - timedelta(days=30)).isoformat(),))
            return self._structured(
                f"The last 30 days contain {entries} fuel entries with recorded spend of {float(spend):,.2f}.",
                "Fuel efficiency cannot be verified from spend alone; it requires consistent odometer, litres, route/load, and vehicle data.",
                "Record odometer and litres for every fill. Review km/litre by vehicle and investigate exceptions against each vehicle's baseline.",
            )
        if "driver" in text:
            drivers = self._count("SELECT COUNT(*) FROM drivers")
            active_drivers = self._count("SELECT COUNT(*) FROM drivers WHERE LOWER(COALESCE(status, '')) = 'active'")
            return self._structured(
                f"FTMS contains {drivers} driver records, of which {active_drivers} are marked active.",
                "An incomplete driver status or expired licence can create a dispatch compliance risk.",
                "Verify licence expiry and active status before assignment, then match qualified drivers to the required vehicle category and route.",
            )
        return self._structured(
            "FTMS fleet analysis is ready for vehicle status, driver readiness, fuel records, maintenance, and compliance data.",
            "A precise operational conclusion needs the vehicle, period, route, or incident context.",
            "Specify the vehicle plate, date range, or operational issue so I can analyse the relevant FTMS data.",
        )

    def report_answer(self, question):
        text = question.lower()
        today = date.today().isoformat()
        end_30 = (date.today() + timedelta(days=30)).isoformat()

        if re.match(r"^\s*(select|insert|update|delete|drop|alter|pragma)\b", text):
            return self._structured(
                "Raw SQL is not accepted by ANGEL.",
                "Unrestricted SQL can expose, alter, or delete FTMS data.",
                "Use a safe report request such as: vehicles under repair, active vehicles, insurance due, registration due, or open breakdowns.",
            )

        if "under repair" in text or "in repair" in text:
            rows = self._query("""SELECT plate_source, plate_code, plate_number FROM vehicles
                                  WHERE LOWER(COALESCE(status, '')) LIKE '%repair%' ORDER BY plate_number""")
            return self._report_vehicles("Vehicles under repair", rows, "Confirm repair owner, expected release date, and replacement dispatch capacity.")
        if "active" in text and "vehicle" in text:
            rows = self._query("""SELECT plate_source, plate_code, plate_number FROM vehicles
                                  WHERE LOWER(COALESCE(status, '')) = 'active' ORDER BY plate_number""")
            return self._report_vehicles("Active vehicles", rows, "Validate compliance and driver assignment before dispatch.")
        if "insurance" in text and any(term in text for term in ("expired", "due", "expire", "renewal")):
            rows = self._query("""SELECT v.plate_source, v.plate_code, v.plate_number, i.expiry_date
                                  FROM vehicle_insurance i JOIN vehicles v ON v.id = i.vehicle_id
                                  WHERE DATE(i.expiry_date) <= DATE(?) ORDER BY i.expiry_date""", (end_30,))
            items = self._format_rows(rows, include_date=True)
            return self._structured(
                f"Insurance report: {len(rows)} policy record(s) expire by {end_30}. {items}",
                "Expired or near-expiry insurance can stop a vehicle from being dispatched and increase exposure.",
                "Prioritise expired policies first, secure renewal confirmation, and update the insurance record in FTMS.",
            )
        if any(term in text for term in ("registration", "mulkiya")):
            rows = self._query("""SELECT plate_source, plate_code, plate_number, mulkiya_expiry_date FROM vehicles
                                  WHERE DATE(mulkiya_expiry_date) <= DATE(?) ORDER BY mulkiya_expiry_date""", (end_30,))
            items = self._format_rows(rows, include_date=True)
            return self._structured(
                f"Registration report: {len(rows)} vehicle(s) have registration expiring by {end_30}. {items}",
                "Expired registration creates a compliance and dispatch risk.",
                "Schedule inspection and renewal early, settle any fines, and update the Mulkiya expiry date after renewal.",
            )
        if "breakdown" in text:
            rows = self._query("""SELECT b.breakdown_date, v.plate_number, b.problem_description, b.status
                                  FROM breakdowns b LEFT JOIN vehicles v ON v.id = b.vehicle_id
                                  WHERE LOWER(COALESCE(b.status, 'open')) NOT IN ('closed', 'resolved', 'completed')
                                  ORDER BY b.breakdown_date DESC""")
            return self._structured(
                f"Breakdown report: {len(rows)} open record(s). {self._format_rows(rows, limit=5)}",
                "Open breakdown records represent downtime and may indicate repeat mechanical or preventive-maintenance issues.",
                "Assign an owner and target completion for each open record; review recurring faults by vehicle and repair type.",
            )
        return self._structured(
            "I can produce predefined safe reports from FTMS; raw SQL is not accepted.",
            "A report requires a recognised fleet condition or compliance topic.",
            "Ask for active vehicles, vehicles under repair, insurance due, registration due, or open breakdowns.",
        )

    def technical_answer(self, question):
        text = question.lower()
        if "chiller" in text or "temperature" in text:
            return self._structured(
                "A chiller temperature fall or inability to hold setpoint can compromise cold-chain cargo. Treat it as a dispatch-critical exception until temperature is verified.",
                "Low refrigerant, compressor or clutch failure, blocked condenser airflow, failed fan, electrical/relay fault, door leakage, incorrect setpoint, or a faulty temperature sensor.",
                "Verify the independent cargo temperature and setpoint; protect or transfer temperature-sensitive cargo; inspect power supply, alarms, fans, condenser cleanliness and doors. Arrange qualified refrigeration diagnosis before the next temperature-controlled trip.",
            )
        if "fuel" in text:
            return self._structured(
                "A sudden fuel-efficiency decline should be investigated against km/litre, route, payload, idling time, and fuel-fill records—not cost alone.",
                "Fuel leak, unauthorised use, incorrect odometer or litres entry, tyre under-inflation, air-filter restriction, injector or engine fault, excess idling, traffic, changed route, or heavier payload.",
                "Check for leaks and safe fuel-level loss immediately. Validate the last fills and odometer readings, compare km/litre to the vehicle baseline, inspect tyres and air filter, then escalate persistent deviation to maintenance.",
            )
        if "tyre" in text or "tire" in text:
            return self._structured(
                "Abnormal tyre wear increases tyre-failure, braking, and fuel-consumption risk.",
                "Incorrect pressure, wheel misalignment, suspension wear, overloading, poor rotation practice, or aggressive driving.",
                "Inspect pressure, tread depth, sidewall damage and wheel nuts before dispatch. Correct pressure, perform alignment/suspension inspection, rotate tyres where appropriate, and remove damaged tyres from service.",
            )
        if "battery" in text:
            return self._structured(
                "Repeated battery failure normally indicates a charging-system, connection, or parasitic-load issue rather than only a weak battery.",
                "Loose/corroded terminals, alternator undercharge, belt fault, excessive standby draw, age, or unsuitable battery capacity.",
                "Test battery state of health and charging voltage, clean and tighten terminals, inspect the belt, and measure key-off draw. Replace the battery only after confirming the charging system is healthy.",
            )
        return self._structured(
            "The reported fault needs a controlled technical assessment before dispatch.",
            "The symptom, vehicle history, warning lamps, ambient conditions, and recent maintenance can change the diagnosis.",
            "Share the vehicle plate, symptom, warning indicators, operating condition, and when it started. If safety, braking, steering, fuel leakage, or cargo temperature is affected, stop dispatch and inspect first.",
        )

    def _report_vehicles(self, title, rows, recommendation):
        return self._structured(
            f"{title}: {len(rows)} vehicle(s). {self._format_rows(rows)}",
            "Vehicle status is only reliable when operational teams update it immediately after a breakdown, repair, or release to service.",
            recommendation,
        )

    @staticmethod
    def _format_rows(rows, include_date=False, limit=10):
        if not rows:
            return "No matching records were found."
        formatted = []
        for row in rows[:limit]:
            values = [str(value) for value in row if value not in (None, "")]
            formatted.append(" / ".join(values))
        return "Records: " + "; ".join(formatted) + (" …" if len(rows) > limit else "")
