from typing import Literal, Self


class Scope:
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
        self.identifier = identifier

    def __iter__(self):
        yield self.start
        yield self.end

    def __getitem__(self, key: Literal[0, 1]) -> int:
        return self.internals[-key][key]

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}{self.internals}'

    def add_child(self, child: Self) -> Self:
        start, end = self.internals[-1]
        self.depth += child.depth

        if end + 1 < child.start:
            if start != end:
                self.internals.append((end + 1, child.start - 1))
            else:
                self.internals[-1] = (start, child.start - 1)

            self.internals.append(child)
        elif end + 1 == child.start:
            self.internals[-1] = child
        else:
            self.internals.append(child)
        
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
        if self.end + self.depth < value:
            if self.start == self.end:
                self.internals[-1] = (self.start, value)
            else:
                self.internals.append((self.end, value))

