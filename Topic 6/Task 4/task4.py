import sys


def parse_input(user_input: str) -> tuple[str, list[str]]:
    parts = user_input.casefold().split()
    if not parts:
        return "", []
    command, *args = parts
    return command, args


def add_contact(args: list[str], contacts: dict[str, str]) -> str:
    if len(args) != 2:
        return "Invalid command."

    name, phone = args
    name = name.casefold()
    if name in contacts:
        return "Contact already exists."

    contacts[name] = phone
    return "Contact added."


def change_contact(args: list[str], contacts: dict[str, str]) -> str:
    if len(args) != 2:
        return "Invalid command."

    name, phone = args
    name = name.casefold()
    if name not in contacts:
        return "Contact not found."

    contacts[name] = phone
    return "Contact updated."


def show_phone(args: list[str], contacts: dict[str, str]) -> str:
    if len(args) != 1:
        return "Invalid command."

    name = args[0].casefold()
    return contacts.get(name, "Contact not found.")


def show_all(contacts: dict[str, str]) -> str:
    if not contacts:
        return "No contacts found."
    return "\n".join(f"{name}: {phone}" for name, phone in contacts.items())


def main() -> None:
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")

    contacts: dict[str, str] = {}
    print("Welcome to the assistant bot!")

    while True:
        try:
            user_input = input("Enter a command: ")
        except (EOFError, KeyboardInterrupt):
            print("\nGood bye!")
            break

        command, args = parse_input(user_input)

        if command in ("close", "exit") and not args:
            print("Good bye!")
            break
        elif command == "hello" and not args:
            print("How can I help you?")
        elif command == "add":
            print(add_contact(args, contacts))
        elif command == "change":
            print(change_contact(args, contacts))
        elif command == "phone":
            print(show_phone(args, contacts))
        elif command == "all" and not args:
            print(show_all(contacts))
        else:
            print("Invalid command.")


if __name__ == "__main__":
    main()
