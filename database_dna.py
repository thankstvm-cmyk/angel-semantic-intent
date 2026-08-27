"""Live, read-only SQLite schema intelligence for Angel."""

import re
import sqlite3


class DatabaseDNA:
    """Answers database questions from the active FTMS schema, never a hard-coded copy."""

    EXCLUDED_TABLES = {"sqlite_sequence", "VEHICLES_OLD"}

    def __init__(self, db_path):
        self.db_path = str(db_path)

    def _tables(self):
        with sqlite3.connect(self.db_path) as connection:
            rows = connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
            ).fetchall()
        return [name for (name,) in rows if name not in self.EXCLUDED_TABLES]

    def _columns(self, table):
        if table not in self._tables():
            return []
        escaped = table.replace('"', '""')
        with sqlite3.connect(self.db_path) as connection:
            return connection.execute(f'PRAGMA table_info("{escaped}")').fetchall()

    def can_answer(self, question):
        text = question.lower()
        return any(word in text for word in ("table", "schema", "column", "field", "database", "sqlite", "structure"))

    def answer(self, question):
        text = re.sub(r"\s+", " ", question.lower()).strip()
        tables = self._tables()

        if "how many" in text or "count" in text or "number of" in text:
            return (
                f"Database intelligence: FTMS currently uses {len(tables)} active application tables. "
                "`vehicles` is the canonical fleet master table."
            )
        if any(word in text for word in ("column", "field", "structure", "schema")):
            table = self._resolve_table(text, tables)
            if not table:
                return "Please specify the active FTMS table whose columns you need, for example: `vehicles columns`."
            columns = self._columns(table)
            details = ", ".join(f"{row[1]} ({row[2] or 'TEXT'})" for row in columns)
            return f"Database intelligence — `{table}` columns:\n{details}"
        if any(word in text for word in ("list", "show", "which", "names", "them", "those", "these")) or "table" in text:
            return "Certainly. Here are the active FTMS tables:\n" + ", ".join(tables)
        return (
            "Database intelligence: FTMS uses SQLite (`ftms.db`). The `vehicles` table is the active fleet master; "
            "ask for table names or a table's columns for a precise answer."
        )

    @staticmethod
    def _resolve_table(text, tables):
        for table in tables:
            if re.search(rf"\b{re.escape(table.lower())}\b", text):
                return table
        aliases = {"vehicle": "vehicles", "insurance": "vehicle_insurance", "driver": "drivers", "fuel": "fuel_entries"}
        for alias, table in aliases.items():
            if re.search(rf"\b{alias}\b", text) and table in tables:
                return table
        return None
