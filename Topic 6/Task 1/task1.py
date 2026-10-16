from math import isfinite


def total_salary(path) -> tuple[float, float]:
    """Повертає загальну та середню зарплату."""
    total = 0.0
    count = 0

    try:
        with open(path, "r", encoding="utf-8") as salary_file:
            for line_number, line in enumerate(salary_file, start=1):
                line = line.strip()
                if not line:
                    continue

                try:
                    name, salary_text = line.split(",")
                    salary = float(salary_text)
                    if not name.strip() or not isfinite(salary) or salary < 0:
                        raise ValueError
                except ValueError as error:
                    raise ValueError(
                        f"Некоректні дані в рядку {line_number}: "
                        "очікується ім'я та скінченна невід'ємна зарплата через кому."
                    ) from error

                total += salary
                count += 1
    except FileNotFoundError as error:
        raise FileNotFoundError(f"Файл не знайдено: {path}") from error
    except UnicodeError as error:
        raise ValueError(f"Файл має бути в кодуванні UTF-8: {path}") from error
    except OSError as error:
        raise OSError(f"Не вдалося прочитати файл: {path}") from error

    average = total / count if count else 0.0
    return total, average
