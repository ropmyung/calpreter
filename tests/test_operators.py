"""연산자 정의 단위 테스트 (콜백 정확성 + 우선순위/결합 속성)."""
import pytest

from calpreter.operators.base import OperationData
from calpreter.operators.data import add, subtract, multiply, power


DATA = OperationData()


class TestOperatorCallbacks:
    @pytest.mark.parametrize("operator, left, right, expected", [
        (add, 2, 3, 5),
        (subtract, 5, 2, 3),        # subtract 가 a-b 여야 함 (a+b 회귀 방지)
        (subtract, 2, 5, -3),
        (multiply, 4, 3, 12),
        (power, 2, 3, 8),
    ])
    def test_binary_callback(self, operator, left, right, expected):
        assert operator(DATA, left, right) == expected

    def test_operand_order_is_left_then_right(self):
        """첫 위치 인자가 좌변이어야 한다 (인자 이름 뒤바뀜 회귀 방지)."""
        assert subtract(DATA, 10, 3) == 7
        assert power(DATA, 2, 10) == 1024


class TestOperatorMetadata:
    def test_precedence_ordering(self):
        assert add.precedence == subtract.precedence
        assert multiply.precedence > add.precedence
        assert power.precedence > multiply.precedence

    def test_power_is_right_associative(self):
        assert power.right_associative is True
        assert add.right_associative is False
        assert multiply.right_associative is False
