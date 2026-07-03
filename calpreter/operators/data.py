from typing import TypeVar
import math

from .base import binary_operator, unary_operator, get_operator, UnaryOperator

T = TypeVar('T', float, int)

def cut_by_symbol(operator: UnaryOperator, char: str) -> bool:
    return char == operator.symbol

@binary_operator('+', precedence=1)
def add(a: T, b: T) -> T:
    return a + b

@binary_operator('-', precedence=1)
def subtract(a: T, b: T) -> T:
    return a - b

def cut_by_term(operator: UnaryOperator, char: str) -> bool:
    return get_operator(char) in (add, subtract)

@binary_operator('*', precedence=2)
def multiply(a: T, b: T) -> T:
    return a * b

@binary_operator('^', precedence=3, right_associative=True)
def power(a: T, b: T) -> T:
    return a ** b

@unary_operator('|', end_finder=cut_by_symbol, end_index_weight=-1)
def absolute(a: T) -> float:
    return abs(a)

@unary_operator("sin", end_finder=cut_by_term, end_index_weight=-1)
def sin(a: T) -> float:
    return math.sin(a)