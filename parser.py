from typing import Any, Self

from scope import Scope
from operators.base import get_operator, UnaryOperator, BinaryOperator
from operators.data import multiply


__all__ = [
    "ExpressionSyntaxError",
    "Parser"
]

_BRACKETS = {
    "(": ")",
    "{": "}",
    "[": "]",
}

class ExpressionSyntaxError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class TokenizedExpression:
    def __init__(self, unary_operator: UnaryOperator | None = None) -> None:
        self._unary_operator = unary_operator
        self._operands = list[float | str | Self]()
        self._operators = list[BinaryOperator]()

    def __repr__(self) -> str:
        return self.__class__.__name__ + str(self)

    def __str__(self) -> str:
        return (str(self._unary_operator) if self._unary_operator else '') + "(" + self.expression + ")"

    @property
    def expression(self) -> str:
        print(self._operands, self._operators, sep="\n")
        result = ""
        i = 0

        for op in self._operators:
            result += str(self._operands[i]) + str(op)
            i += 1
        
        result += str(self._operands[i])
        
        return result

    def add_operand(self, value: float | str | Self) -> Self:
        self._operands.append(value)

        return self
    
    def add_operator(self, value: BinaryOperator) -> Self:
        self._operators.append(value)

        return self
    
    def parse(self): ...


class Parser:
    def __init__(self, expression: str) -> None:
        self.expression = expression
        self.variables = set[str]()

    def assign_variables(self) -> None:
        var_str = ""

        for i, char in enumerate(self.expression):
            if _BRACKETS.get(char) or get_operator(char) or char.isdigit():
                return
            
            if char == ':':
                if var_str:
                    self.variables.add(var_str)

                self.expression = self.expression[i + 1:]

                break
            
            if char.isspace():
                continue

            if char == ',':
                self.variables.add(var_str)
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

            if closing_bracket is not None:
                if len(stack) == 0 and start + 1 < i:
                    result.append((start, i))

                stack.append(Scope(i + 1, identifier=char))

            elif stack and char == _BRACKETS.get(stack[-1].identifier):
                bracket = stack.pop()
                bracket.end = i

                if stack:
                    stack[-1].add_child(bracket)
                else:
                    result.append(bracket)

                    start = i + 1

        if start < i:
            result.append((start, i + 1))

        return result

    def _process_opr_and_vars(self, result: TokenizedExpression, token_str: str, after_num: bool) -> bool:
        if not token_str:
            return False

        operator = get_operator(token_str)

        if operator is None:
            if token_str in self.variables:
                result.add_operand(token_str)

                if after_num:
                    result.add_operator(multiply)

                return True
            else:
                raise ExpressionSyntaxError(f'Unknown Symbol: {token_str}')

        if isinstance(operator, UnaryOperator) and after_num:
            result.add_operator(multiply)

        result.add_operator(operator)

        return False

    def tokenize(self, scopes: list[Scope | tuple[int, int]]) -> TokenizedExpression:
        result = TokenizedExpression()
        after_num = False

        for scope in scopes:
            if isinstance(scope, Scope):
                result.add_operand(self.tokenize(scope.internals))

                if after_num:
                    result.add_operator(multiply)

                continue

            num_func = int
            num_token = ""
            opr_token = ""
            after_num = False

            for char in self.expression[scope[0]: scope[1]]:
                if char.isdigit():
                    after_num = self._process_opr_and_vars(result, opr_token, after_num) or after_num
                    opr_token = ""
                    num_token += char
                elif char == '.':
                    num_token += char
                    num_func = float
                elif char.isspace():
                    continue
                else:
                    if num_token:
                        result.add_operand(num_func(num_token))
                        num_token = ""
                        num_func = int
                        after_num = True

                    operator = get_operator(char)

                    if operator is None:
                        opr_token += char
                    else:
                        after_num = self._process_opr_and_vars(result, opr_token, after_num) or after_num
                        opr_token = ""

                        result.add_operator(operator)
            else:
                if num_token:
                    result.add_operand(num_func(num_token))
                    after_num = True
                
                after_num = self._process_opr_and_vars(result, opr_token, bool(num_token)) or after_num
        else:
            if after_num:
                result.add_operator(multiply)

        return result

    def parse(self, scoped_expressions: TokenizedExpression | None = None):
        if scoped_expressions is None:
            self.assign_variables()
            scoped_expressions = self.tokenize(self.get_scopes())
        
        return scoped_expressions

