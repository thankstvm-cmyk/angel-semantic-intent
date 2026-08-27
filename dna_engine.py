from .database_dna import DatabaseDNA

# =====================================================
# FTMS FleetPro ANGEL DNA ENGINE
# Version : 1.0
# =====================================================

class DNAEngine:
    
    def __init__(self, db_path):
        self.database = DatabaseDNA(db_path)

    def answer(self, question):
        question = question.lower().strip()
        # Database DNA
        if self.database.can_answer(question):
            return self.database.answer(question)
        return None
