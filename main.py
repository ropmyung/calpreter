from calpreter.parser import Parser

if __name__ == "__main__":
    while True:
        expression = input("식 입력: ")

        if not expression:
            print("종료 중...")
            break

        parser = Parser(expression)

        print(Parser(expression).parse())