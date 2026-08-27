class IntentEngine:
    def detect(self, question):
        q = question.lower()
        if "table" in q:
            return "TABLE_INFO"
        elif "database" in q:
            return "APPLICATION_INFO"
        elif "vehicle" in q:
            return "VEHICLE"
        elif "driver" in q:
            return "DRIVER"
        return "GENERAL"