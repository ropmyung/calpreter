from typing import TypeVar
import math

from .base import binary_operator, unary_operator

T = TypeVar('T', float, int)


@binary_operator('+')
def add(a: T, b: T) -> T:
    return a + b

@binary_operator('-')
def subtract(a: T, b: T) -> T:
    return a + b

@binary_operator('*')
def multiply(a: T, b: T) -> T:
    return a * b

@binary_operator('^')
def power(a: T, b: T) -> T:
    return a ** b

@unary_operator('|', '|')
def absolute(a: T) -> float:
    return abs(a)
