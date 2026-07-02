from typing import Self, Callable, TYPE_CHECKING
from enum import IntEnum

from operators.base import Operator, UnaryOperator, OperationData
from operators.data import multiply


if TYPE_CHECKING:
    from parser import Parser


class ExpressionSyntaxError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class TokenType(IntEnum):
    OPERATOR = 0
    POINT = 3
    UNARY = 2
    BINARY = 3

    SCOPE = 5
    DIGIT = 6
    VARIABLE = 8

    START = 10

    def is_float_component(self) -> bool:
        return self % 3 == 0

    def is_number(self) -> bool:
        return self.is_operand() and self % 2 == 0

    def is_operand(self) -> bool:
        return self // 5 == 1

    def is_operator(self) -> bool:
        return self // 5 == 0


class TokenizedExpression:
    def __init__(self, parser: "Parser") -> None:
        self.parser = parser
        self.last_token = TokenType.START
        self._operands = list[float | str | Self]()
        self._operators = list[Operator]()

    def __repr__(self) -> str:
        return self.__class__.__name__ + str(self)

    def __str__(self) -> str:
        return "(" + self.expression + ")"

    @property
    def expression(self) -> str:
        result = ""
        i = 0

        for op in self._operators:
            if isinstance(op, UnaryOperator):
                result += str(op)
            else:
                result += str(self._operands[i]) + str(op)
                i += 1
        
        result += str(self._operands[i])
        
        return result

    def add_operand(self, value: float | str | Self) -> Self:
        self._operands.append(value)

        return self

    def add_operator(self, value: Operator) -> Self:
        self._operators.append(value)

        return self

    def add_variable(self, name: str) -> None:
        if name in self.parser.variables:
            self.add_operand(name)

            if self.last_token.is_operand():
                self.add_operator(multiply)
            
            self.last_token = TokenType.VARIABLE
        else:
            raise ExpressionSyntaxError(f'Unknown Symbol: {name}')

    def parse(self) -> Callable[[OperationData], float]:
        i = 0
        

        for op in self._operators:
            if isinstance(op, UnaryOperator):
                u_op = op
                value = self._operands[i]

                if isinstance(value, TokenizedExpression):
                    t_value = value

                    def calculate(data: OperationData) -> float:
                        return u_op(data, t_value.parse()(data))
