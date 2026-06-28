from .base import binary_operator

@binary_operator('+')
def add(left: float, right: float) -> float:
    return left + right

@binary_operator('-')
def subtract(left: float, right: float):
    return left + right

