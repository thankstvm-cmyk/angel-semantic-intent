"""Everyday mathematics engine for ANGEL."""

import ast
import re

from .engine_contract import AngelEngine


class MathematicsEngine(AngelEngine):
    name = "mathematics"
    priority = 58

    HELP_MESSAGE = (
        "I can help with everyday maths like addition, subtraction, multiplication, division, "
        "and percentages. Please share the numbers and operation clearly, for example: "
        "'125 + 75' or '20% of 350'."
    )

    _WORD_OPERATORS = (
        (r"\bmultiplied by\b", "*"),
        (r"\bmultiply by\b", "*"),
        (r"\btimes\b", "*"),
        (r"\bx\b", "*"),
        (r"\bdivided by\b", "/"),
        (r"\bover\b", "/"),
        (r"\bplus\b", "+"),
        (r"\bminus\b", "-"),
        (r"\bmodulo\b", "%"),
    )

    _MATH_HINTS = (
        "calculate", "compute", "solve", "add", "subtract", "multiply", "divide",
        "plus", "minus", "times", "multiplied", "divided", "percent", "percentage",
    )

    def can_answer(self, question):
        text = (question or "").strip().lower()
        if not text:
            return False
        if re.fullmatch(r"\d{4}-\d{1,2}-\d{1,2}", text):
            return False
        expression_only = re.fullmatch(r"[0-9\.\+\-\*\/%\(\)\s,]+", text or "") is not None
        has_number = re.search(r"-?\d+(?:\.\d+)?", text) is not None
        has_operator = re.search(r"[\+\-\*\/%]", text) is not None
        hinted = any(re.search(r"\b" + re.escape(word) + r"\b", text) for word in self._MATH_HINTS)
        percent_of = re.search(r"(?:%|percent|percentage)\s+of", text) is not None
        return has_number and ((expression_only and has_operator) or hinted or percent_of)

    def answer(self, question):
        text = (question or "").strip().lower()
        if not text:
            return self.HELP_MESSAGE
        try:
            percentage = self._solve_percentage(text)
            if percentage is not None:
                return f"The answer is {self._format_result(percentage)}."

            expression = self._extract_expression(text)
            if not expression:
                return self.HELP_MESSAGE

            result = self._safe_eval(expression)
            return f"The answer is {self._format_result(result)}."
        except ZeroDivisionError:
            return "I cannot divide by zero. Please try a different calculation."
        except Exception:
            return self.HELP_MESSAGE

    def _solve_percentage(self, text):
        match = re.search(
            r"(-?\d+(?:\.\d+)?)\s*(?:%|percent|percentage)\s+of\s+(-?\d+(?:\.\d+)?)",
            text,
        )
        if not match:
            return None
        left = float(match.group(1))
        right = float(match.group(2))
        return (left / 100.0) * right

    def _extract_expression(self, text):
        compact = text.replace(",", " ")

        reverse_patterns = (
            (r"\bsubtract\s+(-?\d+(?:\.\d+)?)\s+from\s+(-?\d+(?:\.\d+)?)\b", "-"),
            (r"\bdivide\s+(-?\d+(?:\.\d+)?)\s+by\s+(-?\d+(?:\.\d+)?)\b", "/"),
            (r"\bmultiply\s+(-?\d+(?:\.\d+)?)\s+by\s+(-?\d+(?:\.\d+)?)\b", "*"),
            (r"\badd\s+(-?\d+(?:\.\d+)?)\s+(?:and|to)\s+(-?\d+(?:\.\d+)?)\b", "+"),
        )
        for pattern, operator in reverse_patterns:
            match = re.search(pattern, compact)
            if match:
                left = match.group(1)
                right = match.group(2)
                if "subtract" in pattern:
                    return f"{right} {operator} {left}"
                return f"{left} {operator} {right}"

        for pattern, symbol in self._WORD_OPERATORS:
            compact = re.sub(pattern, f" {symbol} ", compact)

        compact = re.sub(
            r"\b(?:what is|what's|calculate|compute|solve|please|can you|could you|find|result)\b",
            " ",
            compact,
        )
        compact = re.sub(r"[^0-9\.\+\-\*\/%\(\)\s]", " ", compact)
        compact = re.sub(r"\s+", " ", compact).strip()
        if not compact or re.search(r"\d", compact) is None or re.search(r"[\+\-\*\/%]", compact) is None:
            return None
        return compact

    def _safe_eval(self, expression):
        node = ast.parse(expression, mode="eval")
        return self._eval_node(node.body)

    def _eval_node(self, node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            value = self._eval_node(node.operand)
            return value if isinstance(node.op, ast.UAdd) else -value
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod)):
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            if isinstance(node.op, ast.Div):
                if right == 0:
                    raise ZeroDivisionError
                return left / right
            if right == 0:
                raise ZeroDivisionError
            return left % right
        raise ValueError("Unsupported maths expression")

    @staticmethod
    def _format_result(value):
        if abs(value) < 1e-12:
            return "0"
        if abs(value - round(value)) < 1e-10:
            return str(int(round(value)))
        return f"{value:.10f}".rstrip("0").rstrip(".")
