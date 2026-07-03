"""수식 → 함수 객체 컴파일 후 실제 계산 결과 검증.

실행: 프로젝트 루트에서 `python -m pytest` 또는 `python -m pytest test`
"""
import math

import pytest

from helpers import evaluate, compile_expression


class TestArithmeticAndPrecedence:
    @pytest.mark.parametrize("expression, expected", [
        ("1+2", 3),
        ("5-2", 3),          # subtract 가 실제로 빼는지 (a+b 버그 회귀 방지)
        ("2*3", 6),
        ("2^3", 8),
        ("1+2*3", 7),        # * 가 + 보다 먼저
        ("2*3+1", 7),
        ("2^2*3", 12),       # ^ 가 * 보다 먼저
        ("1+2*3+4", 11),
        ("10-2-3", 5),
    ])
    def test_binary_precedence(self, expression, expected):
        assert evaluate(expression) == expected


class TestAssociativity:
    @pytest.mark.parametrize("expression, expected", [
        ("10-4-3", 3),       # 좌결합: (10-4)-3
        ("2^3^2", 512),      # 우결합: 2^(3^2) = 2^9
        ("100-10-1", 89),
    ])
    def test_associativity(self, expression, expected):
        assert evaluate(expression) == expected


class TestImplicitMultiplication:
    @pytest.mark.parametrize("expression, expected", [
        ("2(3+4)", 14),      # 숫자 * 괄호
        ("(2)3", 6),         # 괄호 * 숫자
        ("(2+3)(4)", 20),    # 괄호 * 괄호
        ("(1+1)(2+2)", 8),
    ])
    def test_implicit_multiplication(self, expression, expected):
        assert evaluate(expression) == expected

    @pytest.mark.parametrize("expression, variables, expected", [
        ("2x", {"x": 5}, 10),        # 숫자 * 변수
        ("x2", {"x": 5}, 10),        # 변수 * 숫자
        ("xy", {"x": 3, "y": 4}, 12),  # 변수 * 변수
    ])
    def test_implicit_multiplication_with_variables(self, expression, variables, expected):
        assert evaluate(expression, **variables) == expected


class TestParentheses:
    @pytest.mark.parametrize("expression, expected", [
        ("(2+3)*2", 10),
        ("((2+3)*2)", 10),
        ("1+(2*(3+4))", 15),
        ("(((1))+(2))*3", 9),      # 깊은 중첩 + start 프로퍼티 재귀 함정
        ("((1+2))", 3),
    ])
    def test_nested_parentheses(self, expression, expected):
        assert evaluate(expression) == expected


class TestVariables:
    @pytest.mark.parametrize("expression, variables, expected", [
        ("x:x+1", {"x": 4}, 5),
        ("x:x^2+1", {"x": 5}, 26),
        ("x,y:2x+y", {"x": 3, "y": 4}, 10),   # 변수 선언 + 곱하기 생략
        ("x:(x+1)(x-1)", {"x": 4}, 15),
        ("x:x(x+1)(x+2)", {"x": 2}, 24),
        ("a,b,c:a+b*c", {"a": 1, "b": 2, "c": 3}, 7),
    ])
    def test_variables(self, expression, variables, expected):
        assert evaluate(expression, **variables) == expected

    def test_compiled_function_is_reusable(self):
        """한 번 컴파일한 함수를 다른 변수 값으로 반복 호출할 수 있어야 한다."""
        square = compile_expression("x:x^2")

        from calpreter.operators.base import OperationData

        assert [square(OperationData({"x": v})) for v in (1, 2, 3)] == [1, 4, 9]


class TestUnaryOperators:
    @pytest.mark.parametrize("expression, expected", [
        ("sin(0)", 0.0),
        ("2sin(0)+1", 1.0),      # 숫자 * 단항연산자
    ])
    def test_unary(self, expression, expected):
        assert evaluate(expression) == pytest.approx(expected)

    def test_sin_of_pi_half(self):
        assert evaluate("x:sin(x)", x=math.pi / 2) == pytest.approx(1.0)


class TestFloats:
    @pytest.mark.parametrize("expression, expected", [
        ("1.5+2", 3.5),
        ("0.5*4", 2.0),
        ("3.14", 3.14),
    ])
    def test_floats(self, expression, expected):
        assert evaluate(expression) == pytest.approx(expected)

    @pytest.mark.parametrize("expression, variables, expected", [
        ("x:2.5x", {"x": 4}, 10.0),
    ])
    def test_float_with_variable(self, expression, variables, expected):
        assert evaluate(expression, **variables) == pytest.approx(expected)


class TestErrors:
    def test_unknown_symbol_raises(self):
        from calpreter.tokenizer import ExpressionSyntaxError

        with pytest.raises(ExpressionSyntaxError):
            evaluate("unknown+1")

    @pytest.mark.parametrize("expression", [
        "2+",       # 피연산자 부족
        "()",       # 빈 스코프
        "1++2",     # 연산자 뒤 이항연산자
    ])
    def test_malformed_expression_raises(self, expression):
        from calpreter.tokenizer import ExpressionSyntaxError

        with pytest.raises(ExpressionSyntaxError):
            evaluate(expression)
