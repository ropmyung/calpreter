from typing import Callable


OPERATOR_REGISTRY: dict[str, "Operator"] = {}


class Operator[**P, T]:
    def __init__(
        self,
        callback: Callable[P, T],
        symbol: str,
        end_identifier: str | None = None
    ) -> None:
        self.name = callback.__name__
        self.symbol = symbol
        self.end_identifier = end_identifier
        self._callback = callback

        OPERATOR_REGISTRY[symbol] = self

    def __repr__(self) -> str:
        return self.symbol

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> T:
        return self._callback(*args, **kwargs)


def binary_operator(symbol: str):
    def decorator[T](callback: Callable[[T, T], T]) -> Operator[[T, T], T]:
        return Operator(callback, symbol)
    
    return decorator

def unary_operator(start_symbol: str, end_symbol: str | None = None ):
    def decorator[T](callback: Callable[[T], T]):
        return Operator(callback, start_symbol, end_symbol)
    
    return decorator

