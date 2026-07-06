"""Parser.get_scopes 의 괄호 범위 분할 검증.

get_scopes 는 최상위 구간을 (start, end) 튜플과 Scope(괄호) 로 나눈다.
과거 off-by-one 버그(괄호 앞 한 글자 / 마지막 구간 누락)의 회귀를 막는다.
(범위형 단항 연산자의 범위는 get_scopes가 아니라 tokenize가 정한다)
"""
from calpreter.parser import Parser
from calpreter.scope import Scope


def segments(expression: str):
    """get_scopes 결과를 (텍스트 조각 | 'SCOPE') 리스트로 평탄화한다."""
    parser = Parser(expression)
    result = []

    for item in parser.get_scopes():
        if isinstance(item, Scope):
            result.append("SCOPE")
        else:
            result.append(expression[item[0]:item[1]])

    return result


class TestScopeSplitting:
    def test_single_token_kept(self):
        assert segments("7") == ["7"]

    def test_leading_char_before_paren_kept(self):
        # "2(3)" 의 앞 "2" 구간이 사라지면 안 된다.
        assert segments("2(3)") == ["2", "SCOPE"]

    def test_trailing_char_after_paren_kept(self):
        # "(2)3" 의 뒤 "3" 구간이 사라지면 안 된다.
        assert segments("(2)3") == ["SCOPE", "3"]

    def test_scope_between_text(self):
        assert segments("1+(2)+3") == ["1+", "SCOPE", "+3"]

    def test_two_scopes_adjacent(self):
        assert segments("(1)(2)") == ["SCOPE", "SCOPE"]
