from typing import Any, Callable

from scope import Scope
from operators import *


__all__ = [
    "ExpressionSyntaxError",
    "Parser"
]

_BRACKETS = {
    "(": ")",
    "{": "}",
    "[": "]",
}


type ScopedList = list[Operator | Variable | float | ScopedList]


class ExpressionSyntaxError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class Variable:
    def __init__(self, symbol: str) -> None:
        self.symbol = symbol

    def __repr__(self) -> str:
        return self.symbol

    def __call__(self, data: dict[str, int | float]) -> int | float:
        return data[self.symbol]


class Parser:
    def __init__(self, expression: str) -> None:
        self.expression = expression
        self.terms = []
        self.variables: dict[str, Variable] = {}
    
    def assign_variables(self) -> None:
        var_str = ""

        for i, char in enumerate(self.expression):
            if _BRACKETS.get(char) or OPERATOR_REGISTRY.get(char) or char.isdigit():
                return
            
            if char == ':':
                if var_str:
                    self.variables[var_str] = Variable(var_str)

                self.expression = self.expression[i + 1:]

                break
            
            if char.isspace():
                continue

            if char == ',':
                self.variables[var_str] = Variable(var_str)
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
    
    def _process_opr_and_vars(self, result: ScopedList, token_str: str) -> str:
        if token_str:
            opr_or_var = OPERATOR_REGISTRY.get(token_str, self.variables.get(token_str))

            if opr_or_var is None:
                raise ExpressionSyntaxError(f'Unknown Symbol: {token_str}')

            result.append(opr_or_var)

        return ""

    def tokenize(self, scopes: list[Scope | tuple[int, int]]) -> ScopedList:
        result: ScopedList = []
        current_index = 0

        for scope in scopes:
            if isinstance(scope, Scope):
                result.append(self.tokenize(scope.internals))
                continue

            num_func = int
            num_token = ""
            opr_token = ""

            for char in self.expression[scope[0]: scope[1]]:
                current_index += 1

                if char.isdigit():
                    opr_token = self._process_opr_and_vars(result, opr_token)
                    num_token += char
                elif char == '.':
                    num_token += char
                    num_func = float
                elif char.isspace():
                    continue
                else:
                    if num_token:
                        result.append(num_func(num_token))
                        num_token = ""
                        num_func = int

                    operator = OPERATOR_REGISTRY.get(char)

                    if operator is None:
                        opr_token += char
                    else:
                        opr_token = self._process_opr_and_vars(result, opr_token)
                        result.append(operator)
            else:
                if num_token:
                    result.append(num_func(num_token))
                
                self._process_opr_and_vars(result, opr_token)
            
            current_index += 1

        return result

    def parse(self):
        self.assign_variables()
        scoped_expressions = self.tokenize(self.get_scopes())



        def calculator(data: dict[str, int| float]) -> int | float:
            return 1

