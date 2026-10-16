import io
import os
import re
import runpy
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from colorama import Fore, Style


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "Topic 6" / "Task 3" / "task3.py"
task3 = runpy.run_path(str(SCRIPT_PATH))
print_directory_tree = task3["print_directory_tree"]
main = task3["main"]


def without_colors(text):
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


class DirectoryTreeTests(unittest.TestCase):
    def setUp(self):
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        self.root = Path(temporary_directory.name) / "picture"
        self.root.mkdir()

    def render_tree(self):
        output = io.StringIO()
        with redirect_stdout(output):
            result = print_directory_tree(self.root)
        self.assertIsNone(result)
        return output.getvalue()

    def test_renders_example_tree_with_directories_before_files(self):
        logo = self.root / "Logo"
        logo.mkdir()
        for name in ("logo-tm.png", "ibm.svg", "IBM+Logo.png"):
            (logo / name).touch()
        for name in ("mongodb.jpg", "bot-icon.png"):
            (self.root / name).touch()

        self.assertEqual(
            without_colors(self.render_tree()),
            "picture/\n"
            "├── Logo/\n"
            "│   ├── IBM+Logo.png\n"
            "│   ├── ibm.svg\n"
            "│   └── logo-tm.png\n"
            "├── bot-icon.png\n"
            "└── mongodb.jpg\n",
        )

    def test_renders_empty_directory(self):
        self.assertEqual(without_colors(self.render_tree()), "picture/\n")

    def test_renders_filesystem_root_without_extra_separator(self):
        filesystem_root = Path(self.root.anchor)
        output = io.StringIO()
        with patch.object(Path, "iterdir", return_value=iter(())):
            with redirect_stdout(output):
                print_directory_tree(filesystem_root)
        self.assertEqual(without_colors(output.getvalue()), f"{filesystem_root}\n")

    def test_renders_deeply_nested_last_branches(self):
        nested = self.root / "first" / "second"
        nested.mkdir(parents=True)
        (nested / "note.txt").touch()
        self.assertEqual(
            without_colors(self.render_tree()),
            "picture/\n"
            "└── first/\n"
            "    └── second/\n"
            "        └── note.txt\n",
        )

    def test_uses_distinct_colors_and_resets_after_names(self):
        (self.root / "Logo").mkdir()
        (self.root / "image.png").touch()
        output = self.render_tree()
        self.assertIn(f"{Fore.CYAN}picture/{Style.RESET_ALL}", output)
        self.assertIn(f"{Fore.CYAN}Logo/{Style.RESET_ALL}", output)
        self.assertIn(f"{Fore.GREEN}image.png{Style.RESET_ALL}", output)

    def test_includes_unicode_spaces_and_hidden_entries(self):
        (self.root / "Фото котів").mkdir()
        (self.root / "Фото котів" / "Мурчик.png").touch()
        (self.root / ".hidden").touch()
        self.assertEqual(
            without_colors(self.render_tree()),
            "picture/\n"
            "├── Фото котів/\n"
            "│   └── Мурчик.png\n"
            "└── .hidden\n",
        )

    def test_reports_missing_path(self):
        with self.assertRaisesRegex(FileNotFoundError, "Шлях не існує"):
            print_directory_tree(self.root / "missing")

    def test_rejects_file_instead_of_directory(self):
        file_path = self.root / "file.txt"
        file_path.touch()
        with self.assertRaisesRegex(NotADirectoryError, "не веде до директорії"):
            print_directory_tree(file_path)

    def test_propagates_permission_error(self):
        with patch.object(Path, "iterdir", side_effect=PermissionError("Access denied")):
            with redirect_stdout(io.StringIO()):
                with self.assertRaises(PermissionError):
                    print_directory_tree(self.root)

    def test_shows_directory_symlink_without_following_it(self):
        link = self.root / "parent-link"
        try:
            link.symlink_to(self.root, target_is_directory=True)
        except (OSError, NotImplementedError) as error:
            self.skipTest(f"Directory symlinks are unavailable: {error}")
        self.assertEqual(
            without_colors(self.render_tree()),
            "picture/\n└── parent-link/\n",
        )


class DirectoryTreeCommandLineTests(unittest.TestCase):
    def setUp(self):
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        self.working_directory = Path(temporary_directory.name)
        self.root = self.working_directory / "Фото котів"
        self.root.mkdir()
        (self.root / "Мурчик.png").touch()

    def run_script(self, *arguments, env=None):
        return subprocess.run(
            [sys.executable, str(SCRIPT_PATH), *arguments],
            cwd=self.working_directory,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=10,
        )

    def test_accepts_absolute_and_relative_paths_with_spaces(self):
        for argument in (str(self.root), self.root.name):
            with self.subTest(path=argument):
                result = self.run_script(argument)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stderr, "")
                self.assertEqual(
                    without_colors(result.stdout),
                    "Фото котів/\n└── Мурчик.png\n",
                )

    def test_reports_missing_or_extra_arguments(self):
        for arguments in ((), (str(self.root), "extra")):
            with self.subTest(arguments=arguments):
                result = self.run_script(*arguments)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")
                self.assertIn("Використання:", result.stderr)
                self.assertNotIn("Traceback", result.stderr)

    def test_handles_legacy_windows_output_encoding(self):
        environment = {**os.environ, "PYTHONIOENCODING": "cp1252"}
        result = self.run_script(str(self.root), env=environment)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertEqual(
            without_colors(result.stdout),
            "Фото котів/\n└── Мурчик.png\n",
        )

    def test_reports_nonexistent_path(self):
        result = self.run_script("missing")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertIn("Шлях не існує: missing", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_rejects_file_argument(self):
        result = self.run_script(str(self.root / "Мурчик.png"))
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertIn("не веде до директорії", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_main_returns_error_status_for_unreadable_directory(self):
        output = io.StringIO()
        errors = io.StringIO()
        with patch.object(sys, "argv", [str(SCRIPT_PATH), str(self.root)]):
            with patch.object(Path, "iterdir", side_effect=PermissionError("Access denied")):
                with redirect_stdout(output), redirect_stderr(errors):
                    status = main()
        self.assertEqual(status, 1)
        self.assertIn("Помилка:", errors.getvalue())
        self.assertIn("Access denied", errors.getvalue())


if __name__ == "__main__":
    unittest.main()
