"""Extensible, priority-based engine routing for FTMS Angel."""


class EngineRegistry:
    """Route a question to the most suitable registered FTMS capability.

    An engine can provide either ``can_answer(question)`` plus ``answer`` or
    just ``answer``.  A matcher can also be supplied during registration for
    small future modules that do not need a full engine class.  Returning
    ``None`` means "not my question", and Angel safely tries the next engine.
    """

    def __init__(self):
        self._engines = []

    def register(self, name, engine, priority=50, matcher=None):
        self.unregister(name)
        self._engines.append({
            "name": name,
            "engine": engine,
            "priority": priority,
            "matcher": matcher,
        })
        self._engines.sort(key=lambda item: item["priority"], reverse=True)

    def unregister(self, name):
        self._engines = [item for item in self._engines if item["name"] != name]

    def names(self):
        return [item["name"] for item in self._engines]

    def answer(self, question):
        for item in self._engines:
            engine = item["engine"]
            try:
                matcher = item["matcher"]
                if matcher is not None and not matcher(question):
                    continue
                if matcher is None and hasattr(engine, "can_answer") and not engine.can_answer(question):
                    continue
                reply = engine.answer(question)
                if reply:
                    return reply
            except Exception:
                # A new or optional module must never prevent other FTMS
                # intelligence resources from answering the user.
                continue
        return None
