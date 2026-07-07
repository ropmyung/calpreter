from typing import Callable, Self, TYPE_CHECKING

OPERATOR_REGISTRY: dict[str, "Operator"] = {}
CONSTANT_REGISTRY: dict[str, float] = {}


class DataException(Exception):
    def __init__(self, data: str) -> None:
        super().__init__(f'NotFound variable: {data}')


class OperationData(dict[str, float]):
    def __getitem__(self, key: str | float) -> float:
        if isinstance(key, str):
            data = self.get(key)

            if data is None:
                raise DataException(key)

            return data

        return key


class Operator[**P]:
    def __init__(
        self,
        callback: Callable[P, float],
        symbol: str,
        precedence: int = 100
    ) -> None:
        self.symbol = symbol
        self._callback = callback
        self.precedence = precedence
        self.right_associative = False

        OPERATOR_REGISTRY[symbol] = self

    def __str__(self) -> str:
        return self.symbol

    def __repr__(self) -> str:
        return self.symbol

    def __call__(self, data: OperationData, *args: P.args, **kwargs: P.kwargs) -> float:
        return self._callback(*args, **kwargs)
    
    def __eq__(self, value: object) -> bool:
        if isinstance(value, str):
            return self.symbol == value
        elif isinstance(value, Operator):
            return self.symbol == value.symbol

        return NotImplemented


class UnaryOperator(Operator[[float]]):
    """전위 단항 연산자.

    - end_finder가 주어지면 토큰화 단계에서 피연산자 범위가 자동으로 정해진다:
      find_end(char)가 True가 되는 문자 또는 자신이 속한 스코프의 끝에서
      범위가 닫힌다. 종료 문자가 연산자 자신의 기호면(|x|의 닫는 |) 함께
      소비되고, +, - 같은 다른 연산자면 소비되지 않고 바깥 내용으로 남는다.
    - implicit_operator는 피연산자 바로 뒤에 연산자 생략으로 등장했을 때
      삽입될 이항 연산자다. 지정하지 않으면 곱하기가 삽입된다.
      예: 2sin(x) -> 2*sin(x), 단항 마이너스는 덧셈: 2-3 -> 2+(-3)
    """

    def __init__(
        self,
        *,
        callback: Callable[[float], float],
        end_finder: Callable[[Self, str], bool] | None = None,
        symbol: str,
        implicit_operator: "BinaryOperator | None" = None,
        precedence: int = 100
    ) -> None:
        super().__init__(callback, symbol, precedence)

        self.has_end_finder = end_finder is not None
        self.implicit_operator = implicit_operator

        if end_finder is not None:
            def find_end(char: str) -> bool:
                return end_finder(self, char)
    
            self.find_end = find_end
    
    def __call__(self, data: OperationData, value: float) -> float:
        return self._callback(data[value])

    def find_end(self, char: str) -> bool:
        return True


class BinaryOperator(Operator[[float, float]]):
    def __init__(
        self,
        callback: Callable[[float, float], float],
        symbol: str,
        *,
        precedence: int = 1,
        right_associative: bool = False
    ) -> None:
        super().__init__(callback, symbol, precedence)

        self.right_associative = right_associative

    def __call__(self, data: OperationData, left: float | str, right: float | str) -> float:
        return self._callback(data[left], data[right])


def binary_operator(symbol: str, *, precedence: int = 1, right_associative: bool = False):
    def decorator(callback: Callable[[float, float], float]) -> BinaryOperator:
        return BinaryOperator(
            callback,
            symbol,
            precedence=precedence,
            right_associative=right_associative
        )

    return decorator

def unary_operator(
    start_symbol: str,
    *,
    end_finder: Callable[[UnaryOperator, str], bool] | None = None,
    implicit_operator: BinaryOperator | None = None,
    precedence: int = 100
):
    def decorator(callback: Callable[[float], float]) -> UnaryOperator:
        return UnaryOperator(
            callback=callback,
            symbol=start_symbol,
            end_finder=end_finder,
            implicit_operator=implicit_operator,
            precedence=precedence
        )

    return decorator

def get_operator(symbol: str) -> BinaryOperator | UnaryOperator | None:
    operator = OPERATOR_REGISTRY.get(symbol)

    if TYPE_CHECKING:
        if not isinstance(operator, (UnaryOperator, BinaryOperator)) and operator is not None:
            raise NotImplementedError

    return operator


def get_constant(name: str) -> float | None:
    """등록된 상수 값을 반환한다. 없으면 None."""
    return CONSTANT_REGISTRY.get(name)


def constant(name: str, value: float, *aliases: str) -> None:
    """상수를 등록한다. 여러 이름(별칭)을 같은 값에 매길 수 있다.

    예: constant("pi", math.pi, "π") 는 pi 와 π 를 모두 원주율로 등록한다.

    상수 이름은 숫자로 시작할 수 없고, 연산자 기호와 겹칠 수 없다
    (겹치면 연산자가 우선해 상수가 인식되지 않기 때문).
    """
    for key in (name, *aliases):
        if not key or key[0].isdigit():
            raise ValueError(f'Invalid constant name: {key!r}')

        if get_operator(key) is not None:
            raise ValueError(f'Constant name "{key}" collides with an operator.')

        CONSTANT_REGISTRY[key] = float(value)

