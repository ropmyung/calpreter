# calpreter

*[English](README.md) · 한국어*

수식 문자열을 **파이썬 함수 객체로 컴파일**하는 라이브러리입니다. 한 번 컴파일해 두면 재파싱 없이 변수 값만 바꿔 가며 반복 계산할 수 있습니다.

- 🔤 **변수 할당** — `x, y: x^2 + y` 처럼 미지수를 선언
- ✖️ **곱하기 생략** — `2x`, `2(x+1)`, `2sin(x)` 등 계수 표기 지원
- 🧮 **연산자 우선순위·결합** — `1 + 2*3 == 7`, `2^3^2 == 512`(우결합)
- 📐 **단항 연산자와 자동 범위 지정** — 절댓값 `|x-5|`, `sin x + 1`, 단항 마이너스 `-x^2`
- 🔣 **상수** — 내장 `pi`, `e`, `tau`, `π` 및 사용자 정의
- 🧩 **확장 가능** — 커스텀 상수·연산자 등록
- ⚡ **컴파일 후 재사용** — 반환값은 순수 계산만 하는 중첩 클로저

## 설치

```bash
pip install calpreter
```

Python 3.12 이상이 필요합니다.

## 빠른 시작

```python
import calpreter

# 1) 컴파일하면 호출 가능한 Expression 이 나온다
f = calpreter.compile_expression("x: x^2 + 1")

f(x=3)          # 10.0
f({"x": 5})     # 26.0
f.variables     # frozenset({'x'})

# 2) 변수가 여러 개면 선언부에 쉼표로 나열
g = calpreter.compile_expression("x, y: 2x + y")
g(x=3, y=4)     # 10.0

# 3) 변수가 없으면 그냥 상수 계산
calpreter.compile_expression("1 + 2*3")()   # 7
```

같은 식을 여러 값으로 반복 호출할 때 파싱은 한 번만 일어납니다.

```python
square = calpreter.compile_expression("x: x^2")
[square(x=n) for n in range(1, 4)]   # [1, 4, 9]
```

## 문법

### 변수 선언

수식 앞에 `이름들 :` 형태로 미지수를 선언합니다. 선언하지 않은 이름을 쓰면
`ExpressionSyntaxError` 가 발생합니다.

```python
calpreter.compile_expression("a, b, c: a + b*c")(a=1, b=2, c=3)   # 7
```

### 연산자

| 연산자 | 의미 | 우선순위 | 비고 |
|:---:|:---|:---:|:---|
| `+` | 덧셈 | 1 | |
| `-` | 뺄셈 / 단항 마이너스 | 3(단항) | `2-3` 은 `2 + (-3)` 로 처리 |
| `*` | 곱셈 | 2 | |
| `^` | 거듭제곱 | 4 | 우결합 (`2^3^2 == 2^(3^2)`) |
| `\|x\|` | 절댓값 | | 짝이 되는 `\|` 까지가 범위 |
| `sin` | 사인 | | `+`/`-` 이전 또는 스코프 끝까지가 범위 |

괄호는 `()`, `{}`, `[]` 를 쓸 수 있습니다.

### 곱하기 생략

계수(숫자)는 피연산자 **앞**에 붙습니다. 미지수·괄호·함수가 뒤따를 때만 곱셈이 생략됩니다.

```python
calpreter.compile_expression("x: 2x")(x=5)        # 10  (2 * x)
calpreter.compile_expression("x: 2(x+1)")(x=3)    # 8   (2 * (x+1))
calpreter.compile_expression("x, y: xy")(x=3, y=4)  # 12  (x * y)
```

> 순수 숫자끼리(`23`)나 숫자가 뒤에 오는 표기(`x2`)는 지원하지 않습니다.
> 수학에서 `23` 이 `2*3` 이 아닌 것과 같은 이유입니다.

### 단항 연산자 자동 범위 지정

범위형 단항 연산자는 피연산자 범위를 스스로 결정합니다.

```python
import math

calpreter.compile_expression("|3 - 5|")()                 # 2   (abs(3-5))
calpreter.compile_expression("x: |x - 5|")(x=2)           # 3
calpreter.compile_expression("x: sin x + 1")(x=0)         # 1.0 (sin(x) + 1)
calpreter.compile_expression("x: sin 2x + 1")(x=math.pi/2)  # 1.0 (sin(2x) + 1)
```

- `|...|` 는 짝이 되는 `|` 를 만나면 닫힙니다.
- `sin` 은 `+` 나 `-` 를 만나거나, 자신을 감싼 괄호가 닫히거나, 수식이 끝나면 닫힙니다.
- 바깥 범위가 닫히면 안쪽 범위도 함께 닫힙니다 (`sin sin x` → `sin(sin(x))`).

### 단항 마이너스

뺄셈은 음수의 덧셈으로 처리되며, 우선순위는 `*` 와 `^` 사이입니다.

```python
calpreter.compile_expression("-3^2")()        # -9   (-(3^2))
calpreter.compile_expression("-2*3")()        # -6   ((-2)*3)
calpreter.compile_expression("x: -x^2")(x=3)  # -9
calpreter.compile_expression("|-3|")()        # 3
```

### 상수

`pi`(`π`), `e`, `tau`(`τ`)가 내장되어 있습니다. 상수는 값이 컴파일 시점에
확정되는 미지수처럼 동작하며, 곱하기 생략도 됩니다.

```python
import math

calpreter.compile_expression("2pi")()         # 6.283...  (2 * pi)
calpreter.compile_expression("e^2")()         # 7.389...
calpreter.compile_expression("x: pi x")(x=2)  # 6.283...
```

## 확장

top-level API로 커스텀 상수·연산자를 등록할 수 있습니다. 전역 레지스트리에
등록되므로, 한 번 등록하면 이후 모든 `compile_expression` 호출에서 쓸 수 있습니다.

```python
import math
import calpreter

# 상수 (별칭도 가능)
calpreter.constant("phi", (1 + 5 ** 0.5) / 2)

# 이항 연산자 — 두 인자를 받는 함수에 데코레이터
@calpreter.binary_operator("%", precedence=2)
def modulo(a, b):
    return a % b

# 단항 함수 — cut_by_term 은 다음 + 나 - 에서 피연산자 범위를 끊는다
@calpreter.unary_operator("cos", end_finder=calpreter.cut_by_term)
def cosine(a):
    return math.cos(a)

calpreter.compile_expression("2phi")()          # 3.236...
calpreter.compile_expression("2 + 7 % 3")()     # 3
calpreter.compile_expression("x: cos x")(x=0)   # 1.0
```

단항 연산자의 범위 전략은 두 가지가 제공됩니다:

- `cut_by_term` — 다음 `+` 나 `-` 까지가 피연산자 (`sin` 방식).
- `cut_by_symbol` — 연산자 자신의 기호가 한 번 더 나올 때까지가 피연산자 (`|x|` 방식).

## API

### `calpreter.compile_expression(source: str) -> Expression`

수식 문자열을 컴파일해 [`Expression`](calpreter/expression.py) 을 반환합니다.

### `calpreter.Expression`

컴파일된 수식을 나타내는 호출 가능한 객체입니다.

- `expr(values=None, /, **variables) -> float` — 변수 값을 대입해 계산. 딕셔너리와 키워드 인자 모두 지원.
- `expr.variables: frozenset[str]` — 이 수식이 필요로 하는 미지수 집합.
- `expr.source: str` — 원본 수식 문자열.

### 등록

- `calpreter.constant(name, value, *aliases)` — 상수를 하나 이상의 이름으로 등록.
- `calpreter.binary_operator(symbol, *, precedence=1, right_associative=False)` — 두 인자 함수용 데코레이터.
- `calpreter.unary_operator(symbol, *, end_finder=None, implicit_operator=None, precedence=100)` — 한 인자 함수용 데코레이터. `end_finder` 에 `cut_by_term`/`cut_by_symbol` 을 주면 자동 범위가 생긴다.

### 예외

모든 파싱 오류는 `calpreter.ExpressionSyntaxError` 의 하위 클래스입니다.
계산 시점에 필요한 변수 값이 없으면 `calpreter.DataException` 이 발생합니다.

```python
import calpreter

try:
    calpreter.compile_expression("1 ++ 2")
except calpreter.ExpressionSyntaxError as error:
    print(error)
```

## 개발

```bash
git clone https://github.com/ropmyung/calpreter
cd calpreter
pip install -e ".[test]"
pytest
```

## 라이선스

[MIT](LICENSE)
