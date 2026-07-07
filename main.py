"""calpreter 대화형 데모.

수식을 입력하면 컴파일하고, 미지수가 있으면 값을 물어본 뒤 계산한다.
    실행: python main.py
"""
from calpreter import Expression, ExpressionSyntaxError


def main() -> None:
    print("수식을 입력하세요. 빈 줄이면 종료합니다.")
    print("예: 2(3+4),  x: x^2 + 1,  x: sin x + 1\n")

    while True:
        source = input("식 입력: ").strip()

        if not source:
            print("종료 중...")
            break

        try:
            expression = Expression(source)
        except ExpressionSyntaxError as error:
            print(f"  문법 오류: {error}\n")
            continue

        values = {}

        for name in sorted(expression.variables):
            values[name] = float(input(f"  {name} = "))

        print(f"  = {expression(values)}\n")


if __name__ == "__main__":
    main()
