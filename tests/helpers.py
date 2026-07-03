"""테스트 공용 헬퍼."""
from calpreter.operators.base import OperationData
from calpreter.parser import Parser


def evaluate(expression: str, **variables: float) -> float:
    """수식 문자열을 컴파일해 변수 값을 대입한 결과를 반환한다.

    Parser(expr).parse() 는 TokenizedExpression 을 만들고,
    그 .parse() 는 실행 가능한 함수 객체를 만든다.
    """
    tokenized = Parser(expression).parse()
    func = tokenized.parse()

    return func(OperationData(variables))


def compile_expression(expression: str):
    """수식을 함수 객체로만 컴파일해 반환한다 (같은 식을 여러 변수로 재사용할 때)."""
    return Parser(expression).parse().parse()
