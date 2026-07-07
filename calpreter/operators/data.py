from typing import TypeVar
import math

from .base import binary_operator, unary_operator, constant, get_operator, UnaryOperator

T = TypeVar('T', float, int)

# 내장 상수 (미지수처럼 곱셈 생략 가능: 2pi -> 2*pi)
constant('pi', math.pi, 'π')
constant('e', math.e)
constant('tau', math.tau, 'τ')

def cut_by_symbol(operator: UnaryOperator, char: str) -> bool:
    return char == operator.symbol

@binary_operator('+', precedence=1)
def add(a: T, b: T) -> T:
    return a + b

# 뺄셈은 음수의 덧셈으로 처리된다: 2-3 -> 2+(-3)
# 우선순위는 *와 ^ 사이여야 한다: -2x == (-2)*x, -3^2 == -(3^2)
@unary_operator('-', implicit_operator=add, precedence=3)
def negative(a: T) -> T:
    return -a

def cut_by_term(operator: UnaryOperator, char: str) -> bool:
    return get_operator(char) in (add, negative)

@binary_operator('*', precedence=2)
def multiply(a: T, b: T) -> T:
    return a * b

@binary_operator('^', precedence=4, right_associative=True)
def power(a: T, b: T) -> T:
    return a ** b

@unary_operator('|', end_finder=cut_by_symbol)
def absolute(a: T) -> float:
    return abs(a)

@unary_operator("sin", end_finder=cut_by_term)
def sin(a: T) -> float:
    return math.sin(a)