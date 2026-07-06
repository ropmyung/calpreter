"""연산자 정의 단위 테스트 (콜백 정확성 + 우선순위/결합 속성)."""
import pytest

from calpreter.operators.base import OperationData
from calpreter.operators.data import add, negative, multiply, power


DATA = OperationData()


class TestOperatorCallbacks:
    @pytest.mark.parametrize("operator, left, right, expected", [
        (add, 2, 3, 5),
        (multiply, 4, 3, 12),
        (power, 2, 3, 8),
    ])
    def test_binary_callback(self, operator, left, right, expected):
        assert operator(DATA, left, right) == expected

    @pytest.mark.parametrize("value, expected", [
        (3, -3),
        (-5, 5),
        (0, 0),
    ])
    def test_negative_callback(self, value, expected):
        assert negative(DATA, value) == expected

    def test_operand_order_is_left_then_right(self):
        """첫 위치 인자가 좌변이어야 한다 (인자 이름 뒤바뀜 회귀 방지)."""
        assert power(DATA, 2, 10) == 1024


class TestOperatorMetadata:
    def test_precedence_ordering(self):
        # 단항 마이너스는 *와 ^ 사이여야 한다: -2x == (-2)*x, -3^2 == -(3^2)
        assert add.precedence < multiply.precedence
        assert multiply.precedence < negative.precedence
        assert negative.precedence < power.precedence

    def test_power_is_right_associative(self):
        assert power.right_associative is True
        assert add.right_associative is False
        assert multiply.right_associative is False

    def test_negative_implicit_operator_is_add(self):
        """연산자 생략 시 단항 마이너스 앞에는 덧셈이 삽입된다: 2-3 -> 2+(-3)"""
        assert negative.implicit_operator is add
