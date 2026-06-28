from scope import Scope


__all__ = [
    "ExpressionSyntaxError",
    "Parser"
]

_BRACKETS = {
    "(": ")",
    "{": "}",
    "[": "]"
}


type ScopedList = list[str | float | ScopedList]


class ExpressionSyntaxError(Exception):
    def __init__(self, index: int, message: str) -> None:
        super().__init__(f'Incorrect expression syntax at {index}: {message}')


class Parser:
    def __init__(self, expression: str) -> None:
        self.expression = expression
        self.terms = []

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

                stack.append(Scope(i + 1))

            elif stack and char == _BRACKETS.get(self.expression[stack[-1].start - 1]):
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
    
    def tokenize(self, scopes: list[Scope | tuple[int, int]]) -> ScopedList:
        result: ScopedList = []

        for scope in scopes:
            if isinstance(scope, Scope):
                result.append(self.tokenize(scope.internals))
                continue

            num_str = ""
            is_float = False

            for char in self.expression[scope[0]: scope[1]]:
                if char.isdigit():
                    num_str += char
                elif char == '.':
                    num_str += char
                    is_float = True
                elif char.isspace():
                    continue
                else:
                    if num_str:
                        if is_float:
                            result.append(float(num_str))
                            is_float = False
                        else:
                            result.append(int(num_str))

                        num_str = ""
                    
                    result.append(char)
            else:
                if num_str:
                    if is_float:
                        result.append(float(num_str))
                        is_float = False
                    else:
                        result.append(int(num_str))

        return result

    def parse(self):
        print(self.get_scopes())

        scoped_expressions = self.tokenize(self.get_scopes())

        return scoped_expressions

