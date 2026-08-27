"""Database-first expiry and compliance intelligence for ANGEL."""

import sqlite3
from datetime import date, timedelta


class ComplianceIntelligence:
    """Reads only active FTMS compliance records and never changes them."""

    def __init__(self, db_path):
        self.db_path = str(db_path)

    def expiry_alerts(self, category="all"):
        """Return expired and upcoming compliance records grouped by urgency."""
        today = date.today()
        horizon = today + timedelta(days=30)
        results = []
        if category in {"all", "registration"}:
            results.extend(self._registration_alerts(today, horizon))
        if category in {"all", "insurance"}:
            results.extend(self._insurance_alerts(today, horizon))
        return sorted(results, key=lambda alert: (alert["expiry_date"], alert["plate"]))

    def _registration_alerts(self, today, horizon):
        return self._read_alerts(
            """SELECT plate_source, plate_code, plate_number, mulkiya_expiry_date
               FROM vehicles
               WHERE DATE(mulkiya_expiry_date) <= DATE(?)
               ORDER BY DATE(mulkiya_expiry_date), plate_number""",
            (horizon.isoformat(),),
            "Mulkiya registration",
            today,
        )

    def _insurance_alerts(self, today, horizon):
        return self._read_alerts(
            """SELECT v.plate_source, v.plate_code, v.plate_number, i.expiry_date
               FROM vehicle_insurance AS i
               JOIN vehicles AS v ON v.id = i.vehicle_id
               WHERE DATE(i.expiry_date) <= DATE(?)
               ORDER BY DATE(i.expiry_date), v.plate_number""",
            (horizon.isoformat(),),
            "Insurance",
            today,
        )

    def _read_alerts(self, sql, parameters, document_type, today):
        try:
            with sqlite3.connect(self.db_path) as connection:
                rows = connection.execute(sql, parameters).fetchall()
        except sqlite3.Error as error:
            raise RuntimeError("FTMS compliance records could not be read.") from error

        alerts = []
        for source, code, number, raw_expiry in rows:
            expiry = date.fromisoformat(raw_expiry)
            days_remaining = (expiry - today).days
            alerts.append({
                "document_type": document_type,
                "plate": " / ".join(str(value) for value in (source, code, number) if value not in (None, "")),
                "expiry_date": expiry,
                "days_remaining": days_remaining,
                "severity": self._severity(days_remaining),
            })
        return alerts

    @staticmethod
    def _severity(days_remaining):
        if days_remaining < 0:
            return "RED"
        if days_remaining <= 7:
            return "RED"
        return "AMBER"
