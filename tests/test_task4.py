import io
import os
import runpy
import subprocess
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "Topic 6" / "Task 4" / "task4.py"
task4 = runpy.run_path(str(SCRIPT_PATH))
parse_input = task4["parse_input"]
add_contact = task4["add_contact"]
change_contact = task4["change_contact"]
show_phone = task4["show_phone"]
show_all = task4["show_all"]
main = task4["main"]


class ParseInputTests(unittest.TestCase):
    def test_normalizes_command_and_arguments(self):
        self.assertEqual(parse_input("AdD JoHN +380012345678"),
                         ("add", ["john", "+380012345678"]))

    def test_handles_extra_whitespace(self):
        self.assertEqual(parse_input("  CHANGE\tJohn   012345 \n"),
                         ("change", ["john", "012345"]))

    def test_returns_consistent_structure_for_blank_input(self):
        for text in ("", " \t\n"):
            with self.subTest(text=text):
                self.assertEqual(parse_input(text), ("", []))

    def test_handles_command_without_arguments(self):
        self.assertEqual(parse_input("HELLO"), ("hello", []))

    def test_normalizes_unicode_names(self):
        self.assertEqual(parse_input("PHONE ОЛЕКСІЙ"), ("phone", ["олексій"]))


class ContactHandlerTests(unittest.TestCase):
    def test_adds_contact_and_preserves_phone_as_string(self):
        contacts = {}
        self.assertEqual(add_contact(["John", "0123456789"], contacts), "Contact added.")
        self.assertEqual(contacts, {"john": "0123456789"})

    def test_duplicate_contact_does_not_overwrite_existing_phone(self):
        contacts = {"john": "0123456789"}
        self.assertEqual(add_contact(["JOHN", "999"], contacts), "Contact already exists.")
        self.assertEqual(contacts, {"john": "0123456789"})

    def test_changes_existing_contact_case_insensitively(self):
        contacts = {"john": "0123456789", "jane": "111"}
        self.assertEqual(change_contact(["JoHN", "+380012345678"], contacts),
                         "Contact updated.")
        self.assertEqual(contacts, {"john": "+380012345678", "jane": "111"})

    def test_change_does_not_create_missing_contact(self):
        contacts = {"john": "123"}
        self.assertEqual(change_contact(["Jane", "456"], contacts), "Contact not found.")
        self.assertEqual(contacts, {"john": "123"})

    def test_finds_phone_case_insensitively(self):
        self.assertEqual(show_phone(["JOHN"], {"john": "0123456789"}), "0123456789")

    def test_reports_missing_contact_as_string(self):
        self.assertEqual(show_phone(["John"], {}), "Contact not found.")

    def test_show_all_returns_formatted_contacts(self):
        contacts = {"john": "0123456789", "олексій": "+380012345678"}
        self.assertEqual(show_all(contacts), "john: 0123456789\nолексій: +380012345678")

    def test_show_all_returns_string_for_empty_contacts(self):
        self.assertEqual(show_all({}), "No contacts found.")

    def test_invalid_argument_counts_do_not_change_contacts(self):
        cases = (
            (add_contact, ([], ["John"], ["John", "123", "extra"])),
            (change_contact, ([], ["John"], ["John", "123", "extra"])),
            (show_phone, ([], ["John", "extra"])),
        )
        for handler, argument_lists in cases:
            for args in argument_lists:
                with self.subTest(handler=handler.__name__, args=args):
                    contacts = {"john": "0123456789"}
                    self.assertEqual(handler(args, contacts), "Invalid command.")
                    self.assertEqual(contacts, {"john": "0123456789"})

    def test_handlers_return_messages_without_console_interaction(self):
        contacts = {}
        output = io.StringIO()
        with patch("builtins.input", side_effect=AssertionError("Unexpected input")):
            with redirect_stdout(output):
                results = [
                    add_contact(["John", "123"], contacts),
                    change_contact(["John", "456"], contacts),
                    show_phone(["John"], contacts),
                    show_all(contacts),
                ]
        self.assertEqual(output.getvalue(), "")
        for result in results:
            self.assertIsInstance(result, str)


class AssistantBotTests(unittest.TestCase):
    def run_bot(self, commands, env=None):
        return subprocess.run(
            [sys.executable, str(SCRIPT_PATH)],
            input=commands,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=env,
            timeout=10,
        )

    def test_complete_contact_session(self):
        result = self.run_bot(
            "HELLO\nADD John 0123456789\nphone JOHN\n"
            "change jOhN +380012345678\nall\nclose\n"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertEqual(
            result.stdout,
            "Welcome to the assistant bot!\n"
            "Enter a command: How can I help you?\n"
            "Enter a command: Contact added.\n"
            "Enter a command: 0123456789\n"
            "Enter a command: Contact updated.\n"
            "Enter a command: john: +380012345678\n"
            "Enter a command: Good bye!\n",
        )

    def test_both_exit_commands_stop_before_next_command(self):
        for command in ("ExIt", "ClOsE"):
            with self.subTest(command=command):
                result = self.run_bot(f"{command}\nhello\n")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stderr, "")
                self.assertEqual(
                    result.stdout,
                    "Welcome to the assistant bot!\nEnter a command: Good bye!\n",
                )

    def test_invalid_commands_do_not_stop_bot(self):
        commands = (
            "", "unknown", "hello extra", "add", "add John", "add John 123 extra",
            "change", "change John", "change John 123 extra", "phone",
            "phone John extra", "all extra", "exit extra", "close extra",
        )
        result = self.run_bot("\n".join((*commands, "hello", "exit")) + "\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertEqual(result.stdout.count("Invalid command."), len(commands))
        self.assertIn("How can I help you?", result.stdout)
        self.assertTrue(result.stdout.endswith("Good bye!\n"))

    def test_missing_and_duplicate_contacts_do_not_stop_bot(self):
        result = self.run_bot(
            "all\nphone John\nchange John 999\nadd John 0123\n"
            "add JOHN 456\nphone john\nexit\n"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertIn("No contacts found.", result.stdout)
        self.assertEqual(result.stdout.count("Contact not found."), 2)
        self.assertIn("Contact already exists.", result.stdout)
        self.assertIn("Enter a command: 0123\n", result.stdout)
        self.assertTrue(result.stdout.endswith("Good bye!\n"))

    def test_end_of_input_exits_cleanly(self):
        result = self.run_bot("")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertTrue(result.stdout.endswith("Good bye!\n"))

    def test_keyboard_interrupt_exits_cleanly(self):
        output = io.StringIO()
        with patch("builtins.input", side_effect=KeyboardInterrupt):
            with redirect_stdout(output):
                self.assertIsNone(main())
        self.assertIn("Welcome to the assistant bot!", output.getvalue())
        self.assertTrue(output.getvalue().endswith("Good bye!\n"))

    def test_unicode_names_work_with_legacy_windows_encoding(self):
        environment = {**os.environ, "PYTHONIOENCODING": "cp1252"}
        result = self.run_bot(
            "ADD ОЛЕКСІЙ +380012345678\nphone Олексій\nall\nexit\n",
            env=environment,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertIn("Enter a command: +380012345678\n", result.stdout)
        self.assertIn("олексій: +380012345678", result.stdout)


if __name__ == "__main__":
    unittest.main()
