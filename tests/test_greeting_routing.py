import importlib
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_NAME = "angel_runtime"


def load_module(module_name):
    if PACKAGE_NAME not in sys.modules:
        package = types.ModuleType(PACKAGE_NAME)
        package.__path__ = [str(REPO_ROOT)]
        sys.modules[PACKAGE_NAME] = package
    return importlib.import_module(f"{PACKAGE_NAME}.{module_name}")


greeting_classifier_module = load_module("greeting_classifier")
ftmsangel_module = load_module("ftmsangel")
GreetingClassifier = greeting_classifier_module.GreetingClassifier
Angel = ftmsangel_module.Angel
ApprovedInternetLookup = load_module("operations_engine").ApprovedInternetLookup


class GreetingClassifierTests(unittest.TestCase):
    def setUp(self):
        self.classifier = GreetingClassifier()

    def test_classifier_examples(self):
        cases = {
            "hi": "basic_greeting",
            "hai": "basic_greeting",
            "hello": "basic_greeting",
            "hellow": "basic_greeting",
            "hallo": "basic_greeting",
            "good morning": "time_greeting",
            "morning": "time_greeting",
            "good after noon": "time_greeting",
            "good afternoon": "time_greeting",
            "good evening": "time_greeting",
            "how are you": "wellbeing_query",
            "how do you do": "wellbeing_query",
            "how r u": "wellbeing_query",
            "hi, docs for mulkiya renewal": "greeting_plus_task",
            "good evening, chiller passing docs": "greeting_plus_task",
            "bye": "farewell",
            "thanks bye": "farewell",
        }
        for message, expected_class in cases.items():
            with self.subTest(message=message):
                result = self.classifier.classify(message)
                self.assertEqual(result["class"], expected_class)

    def test_classifier_output_contract(self):
        result = self.classifier.classify("hi, docs for mulkiya renewal")
        self.assertGreaterEqual(result["confidence"], 0.75)
        self.assertEqual(result["threshold_band"], "high")
        self.assertTrue(result["should_invoke_task_engine"])
        self.assertIn("mulkiya", result["detected_task_tokens"])
        self.assertEqual(result["response_template_key"], "greeting.plus_task")
        self.assertFalse(result["hard_fail"])


class GreetingRoutingTests(unittest.TestCase):
    def make_angel(self):
        return Angel(parent=None, db_path=":memory:")

    def assert_no_dead_end(self, text):
        lowered = text.lower()
        for banned in (
            "i could not locate",
            "i don't know",
            "no information found",
            "i could not identify the right source",
        ):
            self.assertNotIn(banned, lowered)

    def test_basic_greetings_do_not_use_lookup(self):
        with patch.object(ApprovedInternetLookup, "answer", side_effect=AssertionError("lookup should not run")):
            angel = self.make_angel()
            self.assertEqual(angel.reply("hi"), "Hi! How can I help you today?")
            self.assertEqual(angel.reply("hai"), "Hello! What can I do for you?")

    def test_time_greeting_typo_is_handled_without_dead_end(self):
        with patch.object(ApprovedInternetLookup, "answer", side_effect=AssertionError("lookup should not run")):
            angel = self.make_angel()
            response = angel.reply("good after noon")
        self.assertIn("Good afternoon!", response)
        self.assert_no_dead_end(response)

    def test_wellbeing_query_avoids_long_intro_repetition(self):
        angel = self.make_angel()
        first = angel.reply("how are you?")
        second = angel.reply("how are you?")
        self.assertNotEqual(first, second)
        self.assertIn("thank you", first.lower())
        self.assertIn("what would you like to check", second.lower())

    def test_greeting_plus_mulkiya_task_returns_task_answer_and_prompt(self):
        angel = self.make_angel()
        response = angel.reply("hi, docs for mulkiya renewal")
        self.assertTrue(response.startswith("Hi!"))
        self.assertIn("Mulkiya", response)
        self.assertIn("Would you like suggestions regarding this topic?", response)
        self.assert_no_dead_end(response)

    def test_greeting_plus_task_rescues_dead_end_lookup(self):
        with patch.object(
            ApprovedInternetLookup,
            "answer",
            return_value=(
                "I could not locate a specific official page for that service. "
                "Please provide the exact authority service, emirate, and vehicle or document type so I can refine the lookup."
            ),
        ):
            angel = self.make_angel()
            response = angel.reply("good evening, chiller passing docs")
        self.assertTrue(response.startswith("Good evening!"))
        self.assertIn("exact service or document type", response)
        self.assertIn("Would you like suggestions regarding this topic?", response)
        self.assert_no_dead_end(response)

    def test_farewell_response(self):
        angel = self.make_angel()
        response = angel.reply("thanks bye")
        self.assertIn("thank you", response.lower())


if __name__ == "__main__":
    unittest.main()
