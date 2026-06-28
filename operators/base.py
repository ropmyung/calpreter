from typing import Any, Callable


class Operator[**P, T: float]:
    def __init__(self, symbol: str, callback: Callable[P, T]) -> None:
        self._callback = callback

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> T:
        return self._callback(*args, **kwargs)


def binary_operator(symbol: str):
    def decorator[T: float](callback: Callable[[T, T], T]) -> Operator:
        return Operator(symbol, callback)
    
    return decorator

def unary_operator(name: str):
    def decorator[T: float](callback: Callable[[T], T]):
        return Operator(name, callback)
    
    return decorator