# calpreter

*English · [한국어](README.ko.md)*

Compile math expression strings into **Python function objects**. Parse once, then evaluate repeatedly with different variable values — no re-parsing.

- 🔤 **Variable assignment** — declare unknowns like `x, y: x^2 + y`
- ✖️ **Implicit multiplication** — coefficient notation such as `2x`, `2(x+1)`, `2sin(x)`
- 🧮 **Operator precedence & associativity** — `1 + 2*3 == 7`, `2^3^2 == 512` (right-associative)
- 📐 **Unary operators with automatic ranges** — absolute value `|x-5|`, `sin x + 1`, unary minus `-x^2`
- 🔣 **Constants** — built-in `pi`, `e`, `tau`, `π`, and your own
- 🧩 **Extensible** — register custom constants and operators
- ⚡ **Reusable once compiled** — the returned object is a nested closure that only does arithmetic

## Installation

```bash
pip install calpreter
```

Requires Python 3.12 or later.

## Quick start

```python
import calpreter

# 1) Compiling gives you a callable Expression
f = calpreter.compile_expression("x: x^2 + 1")

f(x=3)          # 10.0
f({"x": 5})     # 26.0
f.variables     # frozenset({'x'})

# 2) List multiple variables in the declaration
g = calpreter.compile_expression("x, y: 2x + y")
g(x=3, y=4)     # 10.0

# 3) No variables means a plain constant
calpreter.compile_expression("1 + 2*3")()   # 7
```

Parsing happens only once, even when you call the same expression many times.

```python
square = calpreter.compile_expression("x: x^2")
[square(x=n) for n in range(1, 4)]   # [1, 4, 9]
```

## Syntax

### Variable declaration

Declare unknowns with a `names :` prefix. Using an undeclared name raises
`ExpressionSyntaxError`.

```python
calpreter.compile_expression("a, b, c: a + b*c")(a=1, b=2, c=3)   # 7
```

### Operators

| Operator | Meaning | Precedence | Notes |
|:---:|:---|:---:|:---|
| `+` | addition | 1 | |
| `-` | subtraction / unary minus | 3 (unary) | `2-3` is handled as `2 + (-3)` |
| `*` | multiplication | 2 | |
| `^` | exponentiation | 4 | right-associative (`2^3^2 == 2^(3^2)`) |
| `\|x\|` | absolute value | | range runs up to the matching `\|` |
| `sin` | sine | | range runs until `+`/`-` or the end of the enclosing scope |

Brackets `()`, `{}`, and `[]` are all supported.

### Implicit multiplication

A numeric coefficient goes **in front** of its operand. Multiplication is omitted
only when an unknown, a bracket, or a function follows.

```python
calpreter.compile_expression("x: 2x")(x=5)          # 10  (2 * x)
calpreter.compile_expression("x: 2(x+1)")(x=3)      # 8   (2 * (x+1))
calpreter.compile_expression("x, y: xy")(x=3, y=4)  # 12  (x * y)
```

> Juxtaposing plain numbers (`23`) or placing a number after an operand (`x2`) is
> not supported — for the same reason `23` does not mean `2*3` in mathematics.

### Automatic ranges for unary operators

Range-based unary operators determine the extent of their operand on their own.

```python
import math

calpreter.compile_expression("|3 - 5|")()                   # 2   (abs(3-5))
calpreter.compile_expression("x: |x - 5|")(x=2)             # 3
calpreter.compile_expression("x: sin x + 1")(x=0)           # 1.0 (sin(x) + 1)
calpreter.compile_expression("x: sin 2x + 1")(x=math.pi/2)  # 1.0 (sin(2x) + 1)
```

- `|...|` closes when it meets the matching `|`.
- `sin` closes on a `+` or `-`, when its enclosing bracket closes, or at the end of the expression.
- Closing an outer range also closes inner ones (`sin sin x` → `sin(sin(x))`).

### Unary minus

Subtraction is treated as adding a negative, with precedence between `*` and `^`.

```python
calpreter.compile_expression("-3^2")()        # -9   (-(3^2))
calpreter.compile_expression("-2*3")()        # -6   ((-2)*3)
calpreter.compile_expression("x: -x^2")(x=3)  # -9
calpreter.compile_expression("|-3|")()        # 3
```

### Constants

`pi` (`π`), `e`, and `tau` (`τ`) are built in. A constant behaves like a bound
variable — its value is baked in at compile time and it accepts implicit
multiplication.

```python
import math

calpreter.compile_expression("2pi")()      # 6.283...  (2 * pi)
calpreter.compile_expression("e^2")()      # 7.389...
calpreter.compile_expression("x: pi x")(x=2)  # 6.283...
```

## Extending

Register your own constants and operators through the top-level API. They live in
a global registry, so registering once makes them available to every subsequent
`compile_expression` call.

```python
import math
import calpreter

# Constant (optionally with aliases)
calpreter.constant("phi", (1 + 5 ** 0.5) / 2)

# Binary operator — decorate a function of two arguments
@calpreter.binary_operator("%", precedence=2)
def modulo(a, b):
    return a % b

# Unary function — `cut_by_term` ends the operand range at the next + or -
@calpreter.unary_operator("cos", end_finder=calpreter.cut_by_term)
def cosine(a):
    return math.cos(a)

calpreter.compile_expression("2phi")()          # 3.236...
calpreter.compile_expression("2 + 7 % 3")()     # 3
calpreter.compile_expression("x: cos x")(x=0)   # 1.0
```

Two range strategies are provided for unary operators:

- `cut_by_term` — the operand runs until the next `+` or `-` (like `sin`).
- `cut_by_symbol` — the operand runs until a second copy of the operator's own symbol (like `|x|`).

## API

### `calpreter.compile_expression(source: str) -> Expression`

Compiles an expression string into an [`Expression`](calpreter/expression.py).

### `calpreter.Expression`

A callable object representing a compiled expression.

- `expr(values=None, /, **variables) -> float` — evaluate with variable values; accepts a dict, keyword arguments, or both.
- `expr.variables: frozenset[str]` — the set of unknowns the expression needs.
- `expr.source: str` — the original expression string.

### Registration

- `calpreter.constant(name, value, *aliases)` — register a constant under one or more names.
- `calpreter.binary_operator(symbol, *, precedence=1, right_associative=False)` — decorator for a two-argument function.
- `calpreter.unary_operator(symbol, *, end_finder=None, implicit_operator=None, precedence=100)` — decorator for a one-argument function. Pass `cut_by_term` or `cut_by_symbol` as `end_finder` to give it an automatic range.

### Exceptions

All parse errors are subclasses of `calpreter.ExpressionSyntaxError`.
If a required variable value is missing at evaluation time, `calpreter.DataException`
is raised.

```python
import calpreter

try:
    calpreter.compile_expression("1 ++ 2")
except calpreter.ExpressionSyntaxError as error:
    print(error)
```

## Development

```bash
git clone https://github.com/ropmyung/calpreter
cd calpreter
pip install -e ".[test]"
pytest
```

## License

[MIT](LICENSE)
