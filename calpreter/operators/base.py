from typing import Callable, Self, overload, TYPE_CHECKING

from calpreter.end_finder import EndFinder

OPERATOR_REGISTRY: dict[str, "Operator"] = {}


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
        precedence: int = 0
    ) -> None:
        self.symbol = symbol
        self._callback = callback
        self.precedence = precedence

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
    def __init__(
        self,
        *,
        callback: Callable[[float], float],
        end_finder: Callable[[Self, str], bool] | None = None,
        symbol: str,
        end_index_weight: int = 0
    ) -> None:
        super().__init__(callback, symbol)

        self.end_index_weight = end_index_weight

        if end_finder is not None:
            def find_end(char: str) -> bool:
                return end_finder(self, char)
    
            self.find_end = find_end
    
    def __call__(self, data: OperationData, value: float) -> float:
        return self._callback(data[value])

    def find_end(self, char: str) -> bool:
        return True

    @property
    def end_finder(self) -> EndFinder:
        return EndFinder(self)


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
    end_index_weight: int = 0,
    end_finder: Callable[[UnaryOperator, str], bool] | None = None
):
    def decorator(callback: Callable[[float], float]) -> UnaryOperator:
        return UnaryOperator(
            callback=callback,
            symbol=start_symbol,
            end_index_weight=end_index_weight,
            end_finder=end_finder
        )
    
    return decorator

def get_operator(symbol: str) -> BinaryOperator | UnaryOperator:
    operator = OPERATOR_REGISTRY.get(symbol)

    if TYPE_CHECKING:
        if not isinstance(operator, (UnaryOperator, BinaryOperator)):
            raise NotImplementedError
    
    return operator

