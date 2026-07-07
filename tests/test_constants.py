"""내장 상수(pi, e, tau, π) 지원 검증."""
import math

import pytest

from calpreter import compile_expression, ExpressionSyntaxError
from .helpers import evaluate


class TestBuiltinConstants:
    @pytest.mark.parametrize("expression, expected", [
        ("pi", math.pi),
        ("π", math.pi),
        ("e", math.e),
        ("tau", math.tau),
        ("pi + e", math.pi + math.e),
        ("e^2", math.e ** 2),
        ("-pi", -math.pi),
    ])
    def test_constant_value(self, expression, expected):
        assert evaluate(expression) == pytest.approx(expected)

    @pytest.mark.parametrize("expression, expected", [
        ("2pi", 2 * math.pi),        # 숫자 계수 * 상수 (곱셈 생략)
        ("2*pi", 2 * math.pi),
    ])
    def test_constant_implicit_multiplication(self, expression, expected):
        assert evaluate(expression) == pytest.approx(expected)

    @pytest.mark.parametrize("expression, variables, expected", [
        ("x: pi x", {"x": 2}, 2 * math.pi),      # 상수 * 변수
        ("x: sin pi x", {"x": 1}, math.sin(math.pi)),
    ])
    def test_constant_with_variable(self, expression, variables, expected):
        assert evaluate(expression, **variables) == pytest.approx(expected)

    def test_constant_inside_unary_range(self):
        assert evaluate("sin pi") == pytest.approx(math.sin(math.pi))


class TestConstantNameRules:
    def test_constant_cannot_be_declared_as_variable(self):
        with pytest.raises(ExpressionSyntaxError):
            compile_expression("pi: pi + 1")
