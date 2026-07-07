from typing import Callable

from calpreter.parser import Parser
from calpreter.operators import OperationData


class Expression:
    """컴파일된 수식을 나타내는 호출 가능한 객체.

    수식 문자열을 한 번 파싱·컴파일해 두고, 호출할 때마다 변수 값만 받아
    결과를 계산한다. 내부적으로는 재파싱 없이 중첩 클로저 하나를 실행한다.

    사용 예::

        expr = Expression("x, y: x^2 + y")
        expr(x=3, y=1)        # 10.0
        expr({"x": 3, "y": 1})  # 10.0
        expr.variables         # frozenset({'x', 'y'})
    """

    def __init__(self, source: str) -> None:
        parser = Parser(source)

        self.source = source
        self._function: Callable[[OperationData], float] = parser.parse()
        # parse()가 변수 선언(`x, y:` 접두사)을 소비하며 채워 둔 미지수 집합
        self.variables = frozenset(parser.variables)

    def __call__(self, values: dict[str, float] | None = None, /, **variables: float) -> float:
        """변수 값을 대입해 수식을 계산한다.

        딕셔너리(`expr({"x": 3})`)나 키워드 인자(`expr(x=3)`) 둘 다 가능하며,
        함께 주면 키워드 인자가 우선한다.
        """
        data = OperationData(values or {})
        data.update(variables)

        return self._function(data)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.source!r})"
