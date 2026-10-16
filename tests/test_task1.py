import runpy
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "Topic 6" / "Task 1" / "task1.py"
total_salary = runpy.run_path(str(SCRIPT_PATH))["total_salary"]


class TotalSalaryTests(unittest.TestCase):
    def setUp(self):
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        self.salary_path = Path(temporary_directory.name) / "salaries.txt"

    def write_salaries(self, content):
        self.salary_path.write_text(content, encoding="utf-8")
        return self.salary_path

    def test_calculates_sample_total_and_average(self):
        path = self.write_salaries(
            "Alex Korp,3000\nNikita Borisenko,2000\nSitarama Raju,1000\n"
        )
        self.assertEqual(total_salary(str(path)), (6000, 2000))

    def test_preserves_fractional_average(self):
        path = self.write_salaries("Alex,1000\nNikita,1001\n")
        self.assertEqual(total_salary(path), (2001, 1000.5))

    def test_calculates_decimal_salaries(self):
        path = self.write_salaries("Alex,1000.25\nNikita,2000.50\n")
        self.assertEqual(total_salary(path), (3000.75, 1500.375))

    def test_accepts_mixed_whole_and_decimal_salaries(self):
        path = self.write_salaries("Alex,1000\nNikita,2000.50\n")
        self.assertEqual(total_salary(path), (3000.5, 1500.25))

    def test_calculates_decimal_tenths(self):
        path = self.write_salaries("Alex,0.1\nNikita,0.2\n")
        total, average = total_salary(path)
        self.assertAlmostEqual(total, 0.3)
        self.assertAlmostEqual(average, 0.15)

    def test_handles_single_developer_without_final_newline(self):
        path = self.write_salaries("Alex,1234")
        self.assertEqual(total_salary(path), (1234, 1234))

    def test_counts_developers_with_zero_salary(self):
        path = self.write_salaries("Alex,0\nNikita,100\n")
        self.assertEqual(total_salary(path), (100, 50))

    def test_returns_zeroes_for_empty_or_blank_file(self):
        for content in ("", "\n \t\n"):
            with self.subTest(content=content):
                path = self.write_salaries(content)
                self.assertEqual(total_salary(path), (0.0, 0.0))

    def test_returns_consistent_types_for_empty_and_nonempty_files(self):
        for content in (
            "",
            "\n \t\n",
            "Alex,0\n",
            "Alex,100\nNikita,101\n",
            "Alex,100.25\nNikita,101.50\n",
            "Alex,100\nNikita,101.50\n",
        ):
            with self.subTest(content=content):
                path = self.write_salaries(content)
                result = total_salary(path)
                self.assertIsInstance(result, tuple)
                self.assertEqual(len(result), 2)
                self.assertIsInstance(result[0], float)
                self.assertIsInstance(result[1], float)

    def test_ignores_blank_lines_between_records(self):
        path = self.write_salaries("\nAlex,100\n \t\nNikita,300\n\n")
        self.assertEqual(total_salary(path), (400, 200))

    def test_reads_utf8_names(self):
        path = self.write_salaries("Олексій Коваль,1000\nІрина Шевченко,2000\n")
        self.assertEqual(total_salary(path), (3000, 1500))

    def test_reads_supplied_file_with_spaces_in_path(self):
        self.salary_path = self.salary_path.with_name("custom salaries.txt")
        path = self.write_salaries("Alex,100\nNikita,300\n")
        self.assertEqual(total_salary(str(path)), (400, 200))

    def test_rejects_invalid_records_with_physical_line_number(self):
        invalid_records = (
            "Alex",
            "Alex,100,200",
            "Alex,",
            "Alex,abc",
            ",100",
            " \t,100",
            "Alex,-1",
            "Alex,-0.5",
            "Alex,nan",
            "Alex,NaN",
            "Alex,inf",
            "Alex,-inf",
            "Alex,Infinity",
            "Alex,1e309",
        )
        for record in invalid_records:
            with self.subTest(record=record):
                path = self.write_salaries(f"Valid,100\n\n{record}\n")
                with self.assertRaisesRegex(ValueError, r"рядку 3\b"):
                    total_salary(path)

    def test_reports_missing_file(self):
        with self.assertRaisesRegex(FileNotFoundError, "Файл не знайдено"):
            total_salary(self.salary_path)

    def test_rejects_invalid_utf8(self):
        self.salary_path.write_bytes(b"\xff\xfe")
        with self.assertRaisesRegex(ValueError, "UTF-8"):
            total_salary(self.salary_path)

    def test_reports_file_read_error(self):
        with self.assertRaisesRegex(OSError, "Не вдалося прочитати файл"):
            total_salary(self.salary_path.parent)


if __name__ == "__main__":
    unittest.main()
