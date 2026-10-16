import runpy
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "Topic 6" / "Task 2" / "task2.py"
get_cats_info = runpy.run_path(str(SCRIPT_PATH))["get_cats_info"]


class GetCatsInfoTests(unittest.TestCase):
    def setUp(self):
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        self.cats_path = Path(temporary_directory.name) / "cats.txt"

    def write_cats(self, content):
        self.cats_path.write_text(content, encoding="utf-8")
        return self.cats_path

    def test_reads_sample_file_in_original_order(self):
        self.assertEqual(
            get_cats_info(SCRIPT_PATH.with_name("cats_file.txt")),
            [
                {"id": "60b90c1c13067a15887e1ae1", "name": "Tayson", "age": "3"},
                {"id": "60b90c2413067a15887e1ae2", "name": "Vika", "age": "1"},
                {"id": "60b90c2e13067a15887e1ae3", "name": "Barsik", "age": "2"},
                {"id": "60b90c3b13067a15887e1ae4", "name": "Simon", "age": "12"},
                {"id": "60b90c4613067a15887e1ae5", "name": "Tessi", "age": "5"},
            ],
        )

    def test_reads_single_record_without_final_newline(self):
        path = self.write_cats("cat-1,Tayson,3")
        self.assertEqual(
            get_cats_info(str(path)),
            [{"id": "cat-1", "name": "Tayson", "age": "3"}],
        )

    def test_accepts_zero_age_as_string(self):
        path = self.write_cats("cat-1,Kitten,0\n")
        self.assertEqual(
            get_cats_info(path), [{"id": "cat-1", "name": "Kitten", "age": "0"}]
        )

    def test_returns_empty_list_for_empty_or_blank_file(self):
        for content in ("", "\n \t\n"):
            with self.subTest(content=content):
                path = self.write_cats(content)
                self.assertEqual(get_cats_info(path), [])

    def test_ignores_blank_lines_between_records(self):
        path = self.write_cats("\ncat-1,Tayson,3\n \t\ncat-2,Vika,1\n\n")
        self.assertEqual(
            get_cats_info(path),
            [
                {"id": "cat-1", "name": "Tayson", "age": "3"},
                {"id": "cat-2", "name": "Vika", "age": "1"},
            ],
        )

    def test_reads_utf8_names(self):
        path = self.write_cats("cat-1,Мурчик,2\n")
        self.assertEqual(
            get_cats_info(path), [{"id": "cat-1", "name": "Мурчик", "age": "2"}]
        )

    def test_trims_whitespace_around_fields(self):
        path = self.write_cats(" cat-1 , Tayson , 3 \n")
        self.assertEqual(
            get_cats_info(path), [{"id": "cat-1", "name": "Tayson", "age": "3"}]
        )

    def test_rejects_invalid_records_with_physical_line_number(self):
        invalid_records = (
            "cat-2",
            "cat-2,Vika",
            "cat-2,Vika,1,extra",
            ",Vika,1",
            " \t,Vika,1",
            "cat-2,,1",
            "cat-2, \t,1",
            "cat-2,Vika,",
            "cat-2,Vika,abc",
            "cat-2,Vika,1.5",
            "cat-2,Vika,-1",
        )
        for record in invalid_records:
            with self.subTest(record=record):
                path = self.write_cats(f"cat-1,Tayson,3\n\n{record}\n")
                with self.assertRaisesRegex(ValueError, r"рядку 3\b"):
                    get_cats_info(path)

    def test_rejects_duplicate_ids(self):
        path = self.write_cats("cat-1,Tayson,3\n\ncat-1,Vika,1\n")
        with self.assertRaisesRegex(ValueError, "Повторний ідентифікатор у рядку 3"):
            get_cats_info(path)

    def test_allows_same_name_for_different_ids(self):
        path = self.write_cats("cat-1,Tayson,3\ncat-2,Tayson,1\n")
        self.assertEqual(
            get_cats_info(path),
            [
                {"id": "cat-1", "name": "Tayson", "age": "3"},
                {"id": "cat-2", "name": "Tayson", "age": "1"},
            ],
        )

    def test_reports_missing_file(self):
        with self.assertRaisesRegex(FileNotFoundError, "Файл не знайдено"):
            get_cats_info(self.cats_path)

    def test_rejects_invalid_utf8(self):
        self.cats_path.write_bytes(b"\xff\xfe")
        with self.assertRaisesRegex(ValueError, "UTF-8"):
            get_cats_info(self.cats_path)

    def test_reports_file_read_error(self):
        with self.assertRaisesRegex(OSError, "Не вдалося прочитати файл"):
            get_cats_info(self.cats_path.parent)

    def test_reads_supplied_file_with_spaces_in_path(self):
        self.cats_path = self.cats_path.with_name("custom cats.txt")
        path = self.write_cats("cat-1,Tayson,3\n")
        self.assertEqual(
            get_cats_info(str(path)),
            [{"id": "cat-1", "name": "Tayson", "age": "3"}],
        )


if __name__ == "__main__":
    unittest.main()
