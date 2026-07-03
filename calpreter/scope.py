from typing import Literal, Self


class Scope:
    """괄호 하나가 감싸는 범위를 나타내는 트리 노드.

    internals는 이 괄호 내부를 텍스트 순서대로 담는 리스트로,
    (start, end) 인덱스 구간 튜플과 자식 Scope가 섞여 있다.
    예: "(1+(2)+3)" 의 바깥 Scope.internals == [(1, 3), Scope(4), (6, 8)]

    - 생성 시 internals는 (start, start) 자리표시자 하나로 시작하며,
      자식이 없는 스코프는 닫힐 때 자리표시자가 실제 내용 구간으로 교체된다.
      따라서 add_child/end setter 시점에 마지막 요소가 튜플이면 항상 자리표시자다.
    - open/close: 이 스코프 자신의 여는 괄호 바로 다음 인덱스 / 닫는 괄호 인덱스.
      close는 닫힐 때(end setter) 기록되며, 부모가 자식 앞뒤에 남은 구간을
      계산하는 기준이 된다. (자식은 부모보다 먼저 닫히므로 항상 설정되어 있다)
    - start/end 프로퍼티: 각각 첫 요소의 시작, 마지막 요소의 끝.
      첫 요소가 자식 Scope면 start는 재귀적으로 가장 안쪽 내용의 시작을
      가리키므로, 이 스코프의 괄호 위치 계산에는 open을 써야 한다.
    - __getitem__: key가 0이면 start, 1이면 end.
      (internals[-key][key] 트릭 — -0 == 0 이므로 0은 첫 요소, 1은 마지막 요소를 가리킴)
    - depth: 이 노드를 포함한 하위 Scope 총 개수.
    """

    def __init__(
        self,
        start: int,
        end: int = 0,
        *,
        identifier: str = "(",
    ) -> None:
        self.internals = list[tuple[int, int] | Self]([(start, end or start)])
        self.children_counts = 0
        self.depth = 1
        self.open = start
        self.close = 0
        self.identifier = identifier

    def __iter__(self):
        yield self.start
        yield self.end

    def __getitem__(self, key: Literal[0, 1]) -> int:
        return self.internals[-key][key]

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}{self.internals}'

    def add_child(self, child: Self) -> Self:
        last = self.internals[-1]
        self.depth += child.depth

        if isinstance(last, Scope):
            # 직전 자식의 닫는 괄호 다음부터 이 자식의 여는 괄호 전까지가 사이 내용
            gap_start = last.close + 1

            if gap_start < child.open - 1:
                self.internals.append((gap_start, child.open - 1))

            self.internals.append(child)
        else:
            # 첫 자식: 자리표시자를 자식 이전 내용 구간으로 교체하거나 자식으로 대체
            start = last[0]

            if start < child.open - 1:
                self.internals[-1] = (start, child.open - 1)
                self.internals.append(child)
            else:
                self.internals[-1] = child

        self.children_counts += 1

        return self

    @property
    def start(self) -> int:
        return self.internals[0][0]

    @property
    def end(self) -> int:
        return self.internals[-1][1]

    @end.setter
    def end(self, value: int) -> None:
        self.close = value
        last = self.internals[-1]

        if isinstance(last, Scope):
            # 마지막 자식의 닫는 괄호 뒤에 꼬리 내용이 남아 있으면 추가
            if last.close + 1 < value:
                self.internals.append((last.close + 1, value))
        elif last[0] < value:
            # 자식이 없는 스코프: 자리표시자를 실제 내용 구간으로 교체
            self.internals[-1] = (last[0], value)

