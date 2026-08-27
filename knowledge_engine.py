"""Compatibility wrapper for the live database intelligence engine."""

import sqlite3
from .database_dna import DatabaseDNA


class FTMSKnowledgeEngine:
    def __init__(self, db_path):
        self.db_path = str(db_path)
        self.dna = DatabaseDNA(db_path)
        self.tables = {}
        self.waiting_for_reply = False

    def load_schema(self):
        with sqlite3.connect(self.db_path) as connection:
            names = [row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")]
            self.tables = {
                name: [row[1] for row in connection.execute(f'PRAGMA table_info("{name.replace(chr(34), chr(34) * 2)}")')]
                for name in names if name not in DatabaseDNA.EXCLUDED_TABLES
            }
        return self.tables

    def get_schema(self):
        return self.tables

    def can_answer(self, question):
        return self.dna.can_answer(question)

    def answer(self, question):
        return self.dna.answer(question)
