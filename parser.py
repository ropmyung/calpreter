from typing import Any, Self

from scope import Scope
from operators.base import get_operator, UnaryOperator, BinaryOperator
from operators.data import multiply
from tokenizer import TokenizedExpression, ExpressionSyntaxError, TokenType

__all__ = [
    "ExpressionSyntaxError",
    "Parser"
]

_BRACKETS = {
    "(": ")",
    "{": "}",
    "[": "]",
}


class Parser:
    def __init__(self, expression: str) -> None:
        self.expression = expression
        self.variables = set[str]()
    
    def add_variable(self, var_name: str) -> None:
        if get_operator(var_name):
            raise ExpressionSyntaxError(f'Variable name "{var_name}" corresponds to an operator.')

        if var_name[0].isdigit():
            raise ExpressionSyntaxError(f'Variable name cannot start with digit: {var_name}')

        self.variables.add(var_name)

    def assign_variables(self) -> None:
        var_str = ""

        for i, char in enumerate(self.expression):
            if _BRACKETS.get(char) or get_operator(char) or char.isdigit():
                return
            
            if char == ':':
                if var_str:
                    self.add_variable(var_str)

                self.expression = self.expression[i + 1:]

                break
            
            if char.isspace():
                continue

            if char == ',':
                self.add_variable(var_str)
                var_str = ""
            else:
                var_str += char

    def get_scopes(self) -> list[Scope | tuple[int, int]]:
        stack: list[Scope] = []
        result: list[Scope | tuple[int, int]] = []
        start = 0
        i = 0

        for i, char in enumerate(self.expression):
            closing_bracket = _BRACKETS.get(char)

            if stack and char == _BRACKETS.get(stack[-1].identifier):
                bracket = stack.pop()
                bracket.end = i

                if stack:
                    stack[-1].add_child(bracket)
                else:
                    result.append(bracket)

                    start = i + 1
            
            elif closing_bracket is not None:
                if len(stack) == 0 and start + 1 < i:
                    result.append((start, i))

                stack.append(Scope(i + 1, identifier=char))

        if start < i:
            result.append((start, i + 1))

        return result

    def tokenize_operator(self, result: TokenizedExpression, opr_str: str) -> bool:
        operator = get_operator(opr_str)

        if operator is None:
            return False

        if isinstance(operator, UnaryOperator) and result.last_token.is_operand():
            result.add_operator(multiply)

        result.add_operator(operator)
        result.last_token = TokenType.OPERATOR

        return True

    def tokenize(self, scopes: list[Scope | tuple[int, int]]) -> TokenizedExpression:
        result = TokenizedExpression(self)

        for scope in scopes:
            if isinstance(scope, Scope):
                result.add_operand(self.tokenize(scope.internals))

                if result.last_token.is_operand():
                    result.add_operator(multiply)

                result.last_token = TokenType.SCOPE

                continue

            num_func = int
            number_str = ""
            opr_or_var_str = ""

            for char in self.expression[scope[0]: scope[1]]:
                if char.isdigit():
                    # 숫자 이전에 연산자가 있었는지 확인 및 추가
                    if opr_or_var_str and not self.tokenize_operator(result, opr_or_var_str):
                        raise ExpressionSyntaxError(
                            f'Invalid Position: digit {char} cannot come after variable "{opr_or_var_str}"'
                        )

                    opr_or_var_str = ""
                    number_str += char
                    result.last_token = TokenType.DIGIT
                elif char == '.':
                    number_str += char
                    num_func = float
                    result.last_token = TokenType.POINT
                elif char.isspace():
                    continue
                else:
                    if number_str:
                        result.add_operand(num_func(number_str))
                        number_str = ""
                        num_func = int

                    operator = get_operator(char)

                    if operator is None:
                        opr_or_var_str += char
                    else:
                        if result.last_token.is_operator():
                            raise ExpressionSyntaxError(f'Invalid Position: {char}')

                        if opr_or_var_str and not self.tokenize_operator(result, opr_or_var_str):
                            result.add_variable(opr_or_var_str)

                        opr_or_var_str = ""

                        result.add_operator(operator)
                        result.last_token = TokenType.OPERATOR

            else:
                if number_str:
                    result.add_operand(num_func(number_str))

                if opr_or_var_str and not self.tokenize_operator(result, opr_or_var_str):
                    result.add_variable(opr_or_var_str)

        return result

    def parse(self, scoped_expressions: TokenizedExpression | None = None):
        if scoped_expressions is None:
            self.assign_variables()
            scoped_expressions = self.tokenize(self.get_scopes())

        return scoped_expressions

