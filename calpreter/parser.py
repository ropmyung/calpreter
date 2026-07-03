from enum import IntEnum

from calpreter.scope import Scope
from calpreter.operators.data import get_operator
from calpreter.tokenizer import TokenizedExpression, ExpressionSyntaxError


__all__ = [
    "ExpressionSyntaxError",
    "Parser"
]

_BRACKETS = {
    "(": ")",
    "{": "}",
    "[": "]",
}


class CharacterType(IntEnum):
    Space = 0
    Digit = 1
    Point = 2
    Symbol = 3



class InvalidPositionError(ExpressionSyntaxError):
    def __init__(self, last_char_type: CharacterType, current_char: str) -> None:
        super().__init__(f'{current_char} cannot come after {last_char_type.name}')


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
                if len(stack) == 0 and start < i:
                    result.append((start, i))

                stack.append(Scope(i + 1, identifier=char))

        if start < len(self.expression):
            result.append((start, len(self.expression)))

        return result

    def tokenize(self, scopes: list[Scope | tuple[int, int]]) -> TokenizedExpression:
        result = TokenizedExpression(self)

        for scope in scopes:
            if isinstance(scope, Scope):
                result.add_scope(self.tokenize(scope.internals))

                continue

            num_func = int
            char = ''
            token_string = ""
            last_char_type = CharacterType.Space

            for char in self.expression[scope[0]: scope[1]]:
                if char.isdigit():
                    if last_char_type is CharacterType.Symbol:
                        result.resolve_unknown(token_string)
                        token_string = ""
                        last_char_type = CharacterType.Space

                    token_string += char
                    last_char_type = CharacterType.Digit
                elif char == '.':
                    if last_char_type is not CharacterType.Digit:
                        raise InvalidPositionError(last_char_type, "Point '.'")

                    num_func = float
                    token_string += char
                    last_char_type = CharacterType.Point
                elif char.isspace():
                    continue
                else:
                    if last_char_type is CharacterType.Digit:
                        result.add_constant(num_func(token_string))
                        token_string = ""
                        last_char_type = CharacterType.Space

                    operator = get_operator(char)

                    if operator is None:
                        if char in self.variables:
                            result.add_variable(char)
                            last_char_type = CharacterType.Space
                        else:
                            token_string += char
                            last_char_type = CharacterType.Symbol
                    else:
                        if last_char_type is CharacterType.Symbol:
                            result.resolve_unknown(token_string)
                            token_string = ""

                        result.add_operator(operator)
                        last_char_type = CharacterType.Space
            else:
                if last_char_type is CharacterType.Digit:
                    result.add_constant(num_func(token_string))
                elif last_char_type is CharacterType.Symbol:
                    result.resolve_unknown(token_string)

        return result

    def parse(self, scoped_expressions: TokenizedExpression | None = None):
        if scoped_expressions is None:
            self.assign_variables()
            scoped_expressions = self.tokenize(self.get_scopes())

        return scoped_expressions

