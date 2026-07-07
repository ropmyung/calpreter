"""calpreter — 수식 문자열을 파이썬 함수 객체로 컴파일하는 라이브러리.

기본 사용법::

    import calpreter

    f = calpreter.compile_expression("x: x^2 + 1")
    f(x=3)   # 10.0

변수 할당, 곱하기 생략, 단항 연산자(절댓값·sin·단항 마이너스)와
자동 범위 지정, 상수(pi, e, tau ...)를 지원한다.

커스텀 상수·연산자 등록::

    import math

    calpreter.constant("phi", (1 + 5 ** 0.5) / 2)

    @calpreter.binary_operator("%", precedence=2)
    def modulo(a, b):
        return a % b

    @calpreter.unary_operator("cos", end_finder=calpreter.cut_by_term)
    def cosine(a):
        return math.cos(a)
"""
from calpreter.expression import Expression
from calpreter.parser import Parser
from calpreter.operators import (
    OperationData,
    DataException,
    BinaryOperator,
    UnaryOperator,
    binary_operator,
    unary_operator,
    constant,
    get_operator,
    get_constant,
    cut_by_symbol,
    cut_by_term,
)
from calpreter.tokenizer import ExpressionSyntaxError

__version__ = "0.1.0"

__all__ = [
    # 핵심 API
    "compile_expression",
    "Expression",
    "Parser",
    "OperationData",
    # 커스텀 상수·연산자 등록
    "constant",
    "binary_operator",
    "unary_operator",
    "cut_by_symbol",
    "cut_by_term",
    "BinaryOperator",
    "UnaryOperator",
    "get_operator",
    "get_constant",
    # 예외
    "ExpressionSyntaxError",
    "DataException",
    "__version__",
]


def compile_expression(source: str) -> Expression:
    """수식 문자열을 컴파일해 호출 가능한 :class:`Expression` 으로 반환한다.

    파싱 오류가 있으면 :class:`ExpressionSyntaxError` 를 발생시킨다.
    """
    return Expression(source)
