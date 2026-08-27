from .engine_contract import AngelEngine


class IntentRouter:
    """The sole classifier and dispatcher for all ANGEL user input.

    The current detector is the ordered ``can_answer`` contract.  An LLM can
    later be injected through ``set_detector`` and return an engine name while
    retaining every engine and handler unchanged.
    """

    def __init__(self, engines=(), detector=None):
        self._engines = []
        self._detector = detector
        for engine in engines:
            self.register(engine)

    def register(self, engine):
        if not isinstance(engine, AngelEngine):
            raise TypeError("ANGEL engines must inherit from AngelEngine.")
        if not getattr(engine, "name", None):
            raise ValueError("ANGEL engines must define a non-empty name.")
        self.unregister(engine.name)
        self._engines.append(engine)
        self._engines.sort(key=lambda item: item.priority, reverse=True)

    def unregister(self, name):
        self._engines = [engine for engine in self._engines if engine.name != name]

    def engine_names(self):
        return [engine.name for engine in self._engines]

    def engine(self, name):
        """Return a registered engine by name for narrowly scoped coordination."""
        return next((engine for engine in self._engines if engine.name == name), None)

    def set_detector(self, detector):
        """Set an optional detector that returns a registered engine name or None."""
        self._detector = detector

    def detect(self, question):
        if self._detector is not None:
            name = self._detector.detect(question, self.engine_names())
            if name in self.engine_names():
                return name
        for engine in self._engines:
            if engine.can_answer(question):
                return engine.name
        return None

    def route(self, question, intent=None):
        """Dispatch to ``intent`` when contextual resolution has selected one."""
        intent = intent or self.detect(question)
        if intent is None:
            return None
        engine = next(engine for engine in self._engines if engine.name == intent)
        return engine.answer(question)
