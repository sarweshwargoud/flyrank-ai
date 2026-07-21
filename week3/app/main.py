def display_menu() -> None:
    print("\nSimple Calculator")
    print("------------------")
    print("1) Add")
    print("2) Subtract")
    print("3) Multiply")
    print("4) Divide")
    print("5) Exit")


def get_number(prompt: str) -> float:
    while True:
        value = input(prompt).strip()
        try:
            return float(value)
        except ValueError:
            print("Invalid number. Please enter a valid numeric value.")


def calculate(choice: str, a: float, b: float) -> float:
    if choice == "1":
        return a + b
    if choice == "2":
        return a - b
    if choice == "3":
        return a * b
    if choice == "4":
        if b == 0:
            raise ZeroDivisionError("Cannot divide by zero")
        return a / b
    raise ValueError("Invalid operation")


def main() -> None:
    while True:
        display_menu()
        choice = input("Choose an operation (1-5): ").strip()

        if choice == "5":
            print("Goodbye!")
            break

        if choice not in {"1", "2", "3", "4"}:
            print("Please choose a number between 1 and 5.")
            continue

        first = get_number("Enter the first number: ")
        second = get_number("Enter the second number: ")

        try:
            result = calculate(choice, first, second)
            print(f"Result: {result}\n")
        except ZeroDivisionError as error:
            print(f"Error: {error}\n")
        except ValueError as error:
            print(f"Error: {error}\n")


if __name__ == "__main__":
    main()
