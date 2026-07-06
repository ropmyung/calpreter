from typing import Callable
from enum import IntEnum

from calpreter.scope import Scope
from calpreter.operators import get_operator, OperationData
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
        """괄호 구조를 Scope 트리와 (start, end) 텍스트 구간으로 분해한다."""
        stack: list[Scope] = []
        result: list[Scope | tuple[int, int]] = []
        start = 0

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
        """스코프 목록을 하나의 TokenizedExpression으로 변환한다.

        범위형 단항 연산자(end_finder 보유)를 만나면 result에 하위 표현식을
        열고 이후 토큰을 그 안에 쌓는다. 범위는 find_end가 True가 되는
        문자나 이 스코프의 끝에서 닫힌다. 괄호 내부는 재귀 호출이 따로
        처리하므로 괄호 안의 문자는 바깥 범위를 끝내지 못한다: sin(x+1)의 +
        """
        result = TokenizedExpression(self)

        for scope in scopes:
            if isinstance(scope, Scope):
                result.current().add_scope(self.tokenize(scope.internals))

                continue

            num_func = int
            token_string = ""
            last_char_type = CharacterType.Space

            for char in self.expression[scope[0]: scope[1]]:
                # 열린 단항 범위가 이 문자에서 끝나면 누적 토큰을 확정하고 닫는다
                if result.range_ends(char):
                    if last_char_type is CharacterType.Digit:
                        result.current().add_constant(num_func(token_string))
                        num_func = int
                    elif last_char_type is CharacterType.Symbol:
                        result.resolve_unknown(token_string)

                    token_string = ""
                    last_char_type = CharacterType.Space

                    if result.close_ranges(char):
                        continue

                if char.isdigit():
                    if last_char_type is CharacterType.Symbol:
                        result.resolve_unknown(token_string)
                        token_string = ""

                    token_string += char
                    last_char_type = CharacterType.Digit
                elif char == '.':
                    if last_char_type is not CharacterType.Digit:
                        raise InvalidPositionError(last_char_type, "Point '.'")

                    num_func = float
                    token_string += char
                    last_char_type = CharacterType.Point
                elif char.isspace():
                    # 공백은 토큰 경계다: sin sin x 처럼 이어지는 토큰을 구분한다
                    if last_char_type is CharacterType.Digit:
                        result.current().add_constant(num_func(token_string))
                        num_func = int
                    elif last_char_type is CharacterType.Symbol:
                        result.resolve_unknown(token_string)

                    token_string = ""
                    last_char_type = CharacterType.Space
                else:
                    # 연산자/변수 앞의 누적 숫자는 상수로 확정한다: 2x -> 2, x
                    if last_char_type is CharacterType.Digit:
                        result.current().add_constant(num_func(token_string))
                        token_string = ""
                        num_func = int
                        last_char_type = CharacterType.Space

                    operator = get_operator(char)

                    if operator is None:
                        if char in self.variables:
                            # 한 글자 변수 앞의 미확정 토큰을 먼저 확정한다: sinx -> sin, x
                            if last_char_type is CharacterType.Symbol:
                                result.resolve_unknown(token_string)
                                token_string = ""

                            result.current().add_variable(char)
                            last_char_type = CharacterType.Space
                        else:
                            token_string += char
                            last_char_type = CharacterType.Symbol
                    else:
                        if last_char_type is CharacterType.Symbol:
                            result.resolve_unknown(token_string)
                            token_string = ""

                        result.apply_operator(operator)
                        last_char_type = CharacterType.Space
            else:
                if last_char_type is CharacterType.Digit:
                    result.current().add_constant(num_func(token_string))
                elif last_char_type is CharacterType.Symbol:
                    result.resolve_unknown(token_string)

        return result

    def parse(self) -> Callable[[OperationData], float]:
        self.assign_variables()

        return self.tokenize(self.get_scopes()).parse()

