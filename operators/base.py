from typing import Any, Callable, overload, TYPE_CHECKING


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
        end_identifier: str | None = None
    ) -> None:
        self.symbol = symbol
        self.end_identifier = end_identifier
        self._callback = callback

        OPERATOR_REGISTRY[symbol] = self

    def __str__(self) -> str:
        return self.symbol

    def __repr__(self) -> str:
        return self.symbol

    def __call__(self, data: OperationData, *args: P.args, **kwargs: P.kwargs) -> float:
        return self._callback(*args, **kwargs)


class InputRange:
    def __init__(self) -> None:
        pass


class UnaryOperator(Operator[[float]]):
    def __init__(
        self,
        callback: Callable[[float], float],
        *,
        start_symbol: str,
        end_symbol: str | None = None,
    ) -> None:
        super().__init__(callback, start_symbol, end_symbol)
    
    def __call__(self, data: OperationData, value: str | float) -> float:
        return self._callback(data[value])


class BinaryOperator(Operator[[float, float]]):
    def __init__(self, callback: Callable[[float, float], float], symbol: str) -> None:
        super().__init__(callback, symbol)

    def __call__(self, data: OperationData, right: float | str, left: float | str) -> float:
        return self._callback(data[right], data[left])


def binary_operator(symbol: str):
    def decorator(callback: Callable[[float, float], float]) -> BinaryOperator:
        return BinaryOperator(callback, symbol)
    
    return decorator

def unary_operator(start_symbol: str, end_symbol: str | None = None ):
    def decorator(callback: Callable[[float], float]) -> UnaryOperator:
        return UnaryOperator(callback, start_symbol=start_symbol, end_symbol=end_symbol)
    
    return decorator

variable = UnaryOperator(lambda x: x, start_symbol='$')

def get_operator(symbol: str) -> BinaryOperator | UnaryOperator:
    operator = OPERATOR_REGISTRY.get(symbol)

    if TYPE_CHECKING:
        if not isinstance(operator, (UnaryOperator, BinaryOperator)):
            raise NotImplementedError
    
    return operator