"""Safe everyday arithmetic support for ANGEL."""

import ast
import re
from decimal import Decimal, InvalidOperation

from .engine_contract import AngelEngine


class MathematicsEngine(AngelEngine):
    name = "mathematics"
    priority = 58
    _TRAILING_QUERY = re.compile(r"\s*(?:=\s*)?\?\s*$")
    _MATH_ONLY = re.compile(r"^[\d\s\.\+\-\*\/%\(\),]+$")
    _SUM_ONLY = re.compile(r"^sum\s*\((.*)\)$", re.I)
    _FALLBACK = (
        "I can solve basic arithmetic like 26+24=?, 10*10, or sum(26,25,30,98.50,10000)."
    )

    def can_answer(self, question):
        expression = self._clean(question)
        if not expression:
            return False
        if self._SUM_ONLY.match(expression):
            return True
        return bool(re.search(r"[\+\-\*\/%]", expression)) and bool(self._MATH_ONLY.match(expression))

    def answer(self, question):
        expression = self._clean(question)
        if not expression:
            return None
        try:
            return self._format_number(self._evaluate(expression))
        except (SyntaxError, ValueError, ZeroDivisionError, InvalidOperation):
            return self._FALLBACK

    @classmethod
    def _clean(cls, question):
        text = (question or "").strip()
        return cls._TRAILING_QUERY.sub("", text).strip()

    def _evaluate(self, expression):
        return self._eval_node(ast.parse(expression, mode="eval").body)

    def _eval_node(self, node):
        if isinstance(node, ast.BinOp):
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            operations = {
                ast.Add: left + right,
                ast.Sub: left - right,
                ast.Mult: left * right,
                ast.Div: left / right,
                ast.Mod: left % right,
            }
            operation = operations.get(type(node.op))
            if operation is None:
                raise ValueError("Unsupported operator.")
            return operation
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            value = self._eval_node(node.operand)
            return value if isinstance(node.op, ast.UAdd) else -value
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id.lower() == "sum":
            if node.keywords:
                raise ValueError("Unsupported function arguments.")
            return sum((self._eval_node(argument) for argument in node.args), Decimal("0"))
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return Decimal(str(node.value))
        raise ValueError("Unsupported expression.")

    @staticmethod
    def _format_number(value):
        normalized = value.normalize()
        return format(normalized, "f").rstrip("0").rstrip(".") if normalized != normalized.to_integral() else format(normalized, "f")
