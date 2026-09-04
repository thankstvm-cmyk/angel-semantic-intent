import sys
import types
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = "angel_semantic_intent"

if PACKAGE not in sys.modules:
    package = types.ModuleType(PACKAGE)
    package.__path__ = [str(ROOT)]
    sys.modules[PACKAGE] = package

from angel_semantic_intent.mathematics_engine import MathematicsEngine


class MathematicsEngineTests(unittest.TestCase):
    def setUp(self):
        self.engine = MathematicsEngine()

    def test_accepts_supported_everyday_math_inputs(self):
        for question in (
            "26+24=?",
            "sum(26,25,30,98.50,10000)?",
            "10*10=?",
            "10%5?",
            "100*5999=?",
            "25+50",
            "1+1?",
        ):
            with self.subTest(question=question):
                self.assertTrue(self.engine.can_answer(question))

    def test_solves_supported_everyday_math_inputs(self):
        answers = {
            "26+24=?": "50",
            "sum(26,25,30,98.50,10000)?": "10179.5",
            "10*10=?": "100",
            "10%5?": "0",
            "100*5999=?": "599900",
            "25+50": "75",
            "1+1?": "2",
            "(10.5+0.5)*2?": "22",
        }
        for question, expected in answers.items():
            with self.subTest(question=question):
                self.assertEqual(self.engine.answer(question), expected)

    def test_rejects_non_math_queries(self):
        self.assertFalse(self.engine.can_answer("hello angel"))

    def test_returns_helpful_fallback_for_invalid_math(self):
        self.assertEqual(
            self.engine.answer("sum(26, hello)?"),
            "I can solve basic arithmetic like 26+24=?, 10*10, or sum(26,25,30,98.50,10000).",
        )


if __name__ == "__main__":
    unittest.main()
