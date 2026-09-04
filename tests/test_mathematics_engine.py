import importlib.util
import sys
import types
import unittest
from pathlib import Path


def _load_module(repo_path, package_name, module_name):
    spec = importlib.util.spec_from_file_location(
        f"{package_name}.{module_name}",
        repo_path / f"{module_name}.py",
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[f"{package_name}.{module_name}"] = module
    spec.loader.exec_module(module)
    return module


class MathematicsEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo_path = Path(__file__).resolve().parents[1]
        cls.package_name = "angel_testpkg"
        package = types.ModuleType(cls.package_name)
        package.__path__ = [str(cls.repo_path)]
        sys.modules[cls.package_name] = package

        _load_module(cls.repo_path, cls.package_name, "engine_contract")
        math_module = _load_module(cls.repo_path, cls.package_name, "mathematics_engine")
        cls.engine = math_module.MathematicsEngine()

    def test_handles_basic_expression(self):
        self.assertTrue(self.engine.can_answer("125 + 75"))
        self.assertEqual(self.engine.answer("125 + 75"), "The answer is 200.")

    def test_handles_simple_word_problem(self):
        self.assertTrue(self.engine.can_answer("subtract 8 from 20"))
        self.assertEqual(self.engine.answer("subtract 8 from 20"), "The answer is 12.")

    def test_handles_percentages(self):
        self.assertTrue(self.engine.can_answer("20% of 350"))
        self.assertEqual(self.engine.answer("20% of 350"), "The answer is 70.")

    def test_handles_division_by_zero_safely(self):
        self.assertTrue(self.engine.can_answer("10 / 0"))
        self.assertEqual(
            self.engine.answer("10 / 0"),
            "I cannot divide by zero. Please try a different calculation.",
        )

    def test_does_not_capture_non_math_requests(self):
        self.assertFalse(self.engine.can_answer("show fleet report for today"))


if __name__ == "__main__":
    unittest.main()
