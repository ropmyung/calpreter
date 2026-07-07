"""라이브러리 사용자가 커스텀 상수·연산자를 등록하는 공개 인터페이스 검증.

전역 레지스트리에 등록되므로 다른 테스트와 겹치지 않는 고유 기호를 쓴다.
"""
import math

import pytest

import calpreter


# --- 등록 (모듈 로드 시 1회) ---
calpreter.constant("phi", (1 + 5 ** 0.5) / 2)


@calpreter.binary_operator("%", precedence=2)
def modulo(a, b):
    return a % b


@calpreter.unary_operator("cos", end_finder=calpreter.cut_by_term)
def cosine(a):
    return math.cos(a)


@calpreter.unary_operator("#", end_finder=calpreter.cut_by_symbol)
def bars(a):
    return abs(a)


class TestCustomConstant:
    def test_value(self):
        assert calpreter.compile_expression("phi")() == pytest.approx((1 + 5 ** 0.5) / 2)

    def test_implicit_multiplication(self):
        assert calpreter.compile_expression("2phi")() == pytest.approx(1 + 5 ** 0.5)

    def test_invalid_name_raises(self):
        with pytest.raises(ValueError):
            calpreter.constant("1bad", 1.0)


class TestCustomBinaryOperator:
    @pytest.mark.parametrize("expression, expected", [
        ("7 % 3", 1),
        ("2 + 7 % 3", 3),      # 우선순위: % (2) > + (1)
        ("8 % 5 % 2", 1),      # 좌결합
    ])
    def test_modulo(self, expression, expected):
        assert calpreter.compile_expression(expression)() == expected


class TestCustomUnaryOperator:
    @pytest.mark.parametrize("expression, variables, expected", [
        ("cos 0", {}, 1.0),
        ("x: cos x + 1", {"x": 0}, 2.0),     # cos(x) + 1
        ("2cos(0)", {}, 2.0),
    ])
    def test_term_ranged(self, expression, variables, expected):
        assert calpreter.compile_expression(expression)(variables) == pytest.approx(expected)

    def test_symbol_ranged(self):
        # 짝이 되는 # 까지가 범위 (절댓값 스타일)
        assert calpreter.compile_expression("#3 - 5#")() == 2
