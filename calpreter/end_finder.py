from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from .operators.base import UnaryOperator


class EndFinder:
    def __init__(self, operator: "UnaryOperator") -> None:
        self.callback = operator.find_end

    def __call__(self, character: str) -> bool:
        return self.callback(character)

