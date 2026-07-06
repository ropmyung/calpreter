from typing import Self, Callable, TYPE_CHECKING
from enum import IntEnum

from calpreter.operators.base import Operator, UnaryOperator, BinaryOperator, OperationData
from calpreter.operators.data import multiply, get_operator


if TYPE_CHECKING:
    from calpreter.parser import Parser


class TokenType(IntEnum):
    """토큰 분류를 값의 산술 성질로 인코딩한 열거형.

    값 배치 규칙 (술어 메서드가 이 규칙에 의존하므로 값 변경 시 주의):
    - 0 <= 값 <= 4  (`값 // 5 == 0`): 연산자 계열 (OPERATOR, UNARY, POINT, BINARY)
    - 5 <= 값 <= 9  (`값 // 5 == 1`): 피연산자 계열 (SCOPE, DIGIT, VARIABLE)
    - 값 >= 10: 어느 쪽도 아닌 상태 (START)
    - `값 % 3 == 0`: 실수 리터럴의 구성 요소 (POINT=3, DIGIT=6)
    - 피연산자 중 `값 % 2 == 0`: 숫자로 취급 (DIGIT=6, VARIABLE=8 — 미지수도 숫자)

    주의: 0은 모든 수로 나누어떨어지므로 연산자 계열에 0을 쓰면
    is_float_component 등 나머지 기반 술어가 오판한다. (그래서 OPERATOR = 1)
    """
    OPERATOR = 1
    UNARY = 2
    BINARY = 3

    SCOPE = 5
    CONSTANT = 6
    VARIABLE = 8

    START = 10

    def is_number(self) -> bool:
        return self.is_operand() and self % 2 == 0

    def is_operand(self) -> bool:
        return self // 5 == 1

    def is_operator(self) -> bool:
        return self // 5 == 0


class ExpressionSyntaxError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(f'{self.__class__.__name__}: {message}')


class UnknownSymbol(ExpressionSyntaxError):
    def __init__(self, symbol_name: str) -> None:
        super().__init__(f'"{symbol_name}" is unknown')


class CoefficientError(ExpressionSyntaxError):
    def __init__(self, number: float, last_token: TokenType) -> None:
        super().__init__(f'Coefficient "{number}" should come before {last_token.name}')


class InvalidPositionError(ExpressionSyntaxError):
    def __init__(self, last_token: TokenType, current_token: TokenType) -> None:
        super().__init__(f'{current_token.name} cannot come after {last_token.name}')


class TokenizedExpression:
    """토큰화된 수식 한 스코프(괄호 범위)를 담는 중간 표현.

    불변식 — _operands와 _operators는 텍스트 등장 순서를 유지하는 병렬 리스트:
    - 이항 연산자는 좌우 피연산자 '사이'에 위치한다.
    - 단항 연산자는 자신이 적용될 피연산자 '앞'에 위치한다.
    - 따라서 len(_operands) == (이항 연산자 개수) + 1 이어야 한다.
    - 피연산자는 숫자 리터럴(float/int), 변수명(str),
      하위 스코프(TokenizedExpression) 중 하나다.

    expression 프로퍼티와 parse는 모두 이 불변식을 전제로 동작한다.
    """

    def __init__(self, parser: "Parser") -> None:
        self.parser = parser
        self._last_token = TokenType.START
        self._operands = list[float | str | Self]()
        self._operators = list[Operator]()
        # 토큰화 중에 열려 있는 단항 연산자 범위들: (연산자, 토큰이 쌓이는 하위 표현식)
        # 스코프별 최상위 표현식만 사용하며, 토큰은 항상 current()에 쌓인다.
        self._open_ranges = list[tuple[UnaryOperator, Self]]()
        self._binary_count = 0

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

    def add_scope(self, value: Self) -> None:
        if self._last_token.is_operand():
            self.add_operator(multiply)

        self._operands.append(value)
        self._last_token = TokenType.SCOPE

    def add_constant(self, value: float) -> None:
        if self._last_token.is_operand():
            raise CoefficientError(value, self._last_token)

        self._operands.append(value)
        self._last_token = TokenType.CONSTANT

    def add_operator(self, value: Operator) -> None:
        if isinstance(value, BinaryOperator):
            # 이항 연산자의 좌변은 피연산자여야 한다: "-3", "1++2" 등 차단
            if not self._last_token.is_operand():
                raise InvalidPositionError(self._last_token, TokenType.BINARY)

            self._last_token = TokenType.BINARY
        else:
            self._last_token = TokenType.UNARY

        self._operators.append(value)

    def add_unary(self, operator: UnaryOperator) -> None:
        """단항 연산자를 추가한다. 직전이 피연산자면 생략된 연산자를 삽입한다.

        삽입할 연산자는 operator.implicit_operator가 정한다.
        (기본은 곱하기: 2|3| -> 2*|3|, 단항 마이너스는 덧셈: 2-3 -> 2+(-3))
        """
        if self._last_token.is_operand():
            self.add_operator(operator.implicit_operator or multiply)

        self.add_operator(operator)

    def add_variable(self, name: str) -> None:
        if name in self.parser.variables:
            self._operands.append(name)

            if self._last_token.is_operand():
                self.add_operator(multiply)
            
            self._last_token = TokenType.VARIABLE
        else:
            raise UnknownSymbol(name)

    def resolve_unknown(self, token_string: str) -> None:
        """여러 글자 토큰을 변수 또는 연산자로 확정한다."""
        operator = get_operator(token_string)

        if operator is None:
            self.current().add_variable(token_string)
        else:
            self.apply_operator(operator)

    def apply_operator(self, operator: Operator) -> None:
        """연산자를 현재 표현식에 적용한다. 범위형 단항 연산자면 범위를 연다."""
        if not isinstance(operator, UnaryOperator):
            self.current().add_operator(operator)
        elif operator.has_end_finder:
            self.open_range(operator)
        else:
            self.current().add_unary(operator)

    def current(self) -> Self:
        """토큰이 쌓일 표현식 — 가장 안쪽에 열린 단항 범위, 없으면 자기 자신."""
        if self._open_ranges:
            return self._open_ranges[-1][1]

        return self

    def open_range(self, operator: UnaryOperator) -> None:
        """범위형 단항 연산자의 범위를 연다.

        하위 표현식을 만들어 현재 위치에 피연산자로 붙이고, 범위가 닫힐
        때까지 이후 토큰은 그 하위 표현식에 쌓인다. 스코프가 끝날 때까지
        닫히지 않은 범위는 그대로 두면 된다 (이미 피연산자로 붙어 있다).
        """
        target = self.current()
        sub = self.__class__(self.parser)

        target.add_unary(operator)
        target.add_scope(sub)

        self._open_ranges.append((operator, sub))

    def range_ends(self, char: str) -> bool:
        """열려 있는 단항 범위 중 char로 끝나는 것이 있는지 확인한다."""
        return self._find_range_end(char) is not None

    def close_ranges(self, char: str) -> bool:
        """char로 끝나는 단항 범위들을 닫는다. 문자를 소비했으면 True.

        바깥 범위가 끝나면 안쪽 범위들도 함께 끝나고(|sin x|의 닫는 |),
        소비되지 않은 문자는 남은 범위를 연달아 끝낼 수 있다(sin sin x + 1의 +).
        """
        consumed = False

        while not consumed:
            depth = self._find_range_end(char)

            if depth is None:
                break

            # depth보다 안쪽(위)의 범위들은 바깥 범위가 끝나면서 함께 닫힌다
            del self._open_ranges[depth + 1:]

            operator, _ = self._open_ranges.pop()
            consumed = char == operator.symbol

        return consumed

    def _find_range_end(self, char: str) -> int | None:
        """가장 안쪽부터 검사해 char로 끝나는 첫 범위의 깊이를 찾는다."""
        for depth in range(len(self._open_ranges) - 1, -1, -1):
            if self._open_ranges[depth][0].find_end(char):
                return depth

        return None

    def parse(self) -> Callable[[OperationData], float]:
        """토큰들을 연산자 우선순위에 따라 중첩 클로저 하나로 컴파일한다.

        셔팅야드(shunting-yard) 알고리즘을 병렬 리스트 구조에 맞게 적용:
        연산자 리스트를 순회하며 우선순위가 높은 연산자부터 클로저로
        묶는다(reduce). 하위 스코프는 이 시점에 재귀적으로 한 번만
        컴파일되므로, 반환된 함수는 반복문·파싱 없이
        `op1(data, op2(data, ...))` 형태의 순수 연산 호출만 수행한다.
        """
        if not self._operands:
            raise ExpressionSyntaxError('Empty expression')

        if self._last_token.is_operator():
            raise ExpressionSyntaxError(f'{self._last_token.name} cannot come last')

        # 컴파일된 노드(피연산자) 스택과 결합 대기 중인 연산자 스택
        output = list[Callable[[OperationData], float]]()
        waiting = list[Operator]()

        def push_operand(value: float | str | Self) -> None:
            if isinstance(value, TokenizedExpression):
                output.append(value.parse())
            else:
                # float은 그대로, str은 변수로 — 해석은 호출 시점에 OperationData가 담당
                output.append(lambda data, value=value: data[value])

        def reduce() -> None:
            op = waiting.pop()

            if isinstance(op, UnaryOperator):
                operand = output.pop()
                output.append(
                    lambda data, op=op, operand=operand: op(data, operand(data))
                )
            else:
                right = output.pop()
                left = output.pop()
                output.append(
                    lambda data, op=op, left=left, right=right:
                        op(data, left(data), right(data))
                )

        def binds_tighter(top: Operator, incoming: BinaryOperator) -> bool:
            if incoming.right_associative:
                return top.precedence > incoming.precedence

            return top.precedence >= incoming.precedence

        operands = iter(self._operands)

        for op in self._operators:
            if isinstance(op, UnaryOperator):
                waiting.append(op)
                continue

            if TYPE_CHECKING and not isinstance(op, BinaryOperator):
                return NotImplemented

            # 이 이항 연산자의 좌변 피연산자
            push_operand(next(operands))

            while waiting and binds_tighter(waiting[-1], op):
                reduce()

            waiting.append(op)

        push_operand(next(operands))

        while waiting:
            reduce()

        return output[0]

