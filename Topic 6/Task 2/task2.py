def get_cats_info(path) -> list[dict[str, str]]:
    """Повертає список словників із даними котів."""
    cats = []
    seen_ids = set()

    try:
        with open(path, "r", encoding="utf-8") as cats_file:
            for line_number, line in enumerate(cats_file, start=1):
                line = line.strip()
                if not line:
                    continue

                try:
                    cat_id, name, age = [part.strip() for part in line.split(",")]
                    if not cat_id or not name or int(age) < 0:
                        raise ValueError
                except ValueError as error:
                    raise ValueError(
                        f"Некоректні дані в рядку {line_number}: "
                        "очікується ідентифікатор, ім'я та цілий невід'ємний вік через кому."
                    ) from error

                if cat_id in seen_ids:
                    raise ValueError(
                        f"Повторний ідентифікатор у рядку {line_number}: {cat_id}"
                    )

                cats.append({"id": cat_id, "name": name, "age": age})
                seen_ids.add(cat_id)
    except FileNotFoundError as error:
        raise FileNotFoundError(f"Файл не знайдено: {path}") from error
    except UnicodeError as error:
        raise ValueError(f"Файл має бути в кодуванні UTF-8: {path}") from error
    except OSError as error:
        raise OSError(f"Не вдалося прочитати файл: {path}") from error

    return cats
