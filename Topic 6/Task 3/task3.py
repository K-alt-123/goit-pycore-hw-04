import sys
from pathlib import Path
from stat import S_ISDIR

from colorama import Fore, Style, just_fix_windows_console


def print_directory_tree(path: str | Path) -> None:
    """Друкує кольорове дерево директорії."""
    try:
        directory = Path(path).expanduser().resolve(strict=True)
    except FileNotFoundError as error:
        raise FileNotFoundError(f"Шлях не існує: {path}") from error

    if not S_ISDIR(directory.stat().st_mode):
        raise NotADirectoryError(f"Шлях не веде до директорії: {path}")

    root_name = f"{directory.name}/" if directory.name else str(directory)
    print(f"{Fore.CYAN}{root_name}{Style.RESET_ALL}")
    _print_contents(directory, "", {directory})


def _print_contents(directory: Path, prefix: str, ancestors: set[Path]) -> None:
    entries = sorted(
        directory.iterdir(),
        key=lambda entry: (not entry.is_dir(), entry.name.casefold(), entry.name),
    )

    for index, entry in enumerate(entries):
        is_last = index == len(entries) - 1
        branch = "└── " if is_last else "├── "
        is_directory = entry.is_dir()
        color = Fore.CYAN if is_directory else Fore.GREEN
        name = f"{entry.name}/" if is_directory else entry.name
        print(f"{prefix}{branch}{color}{name}{Style.RESET_ALL}")

        # Не обходимо посилання та циклічні шляхи.
        if is_directory and not entry.is_symlink():
            target = entry.resolve()
            if target not in ancestors:
                next_prefix = prefix + ("    " if is_last else "│   ")
                _print_contents(entry, next_prefix, ancestors | {target})


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    just_fix_windows_console()

    if len(sys.argv) != 2:
        print(
            f'Використання: python "{sys.argv[0]}" <шлях_до_директорії>',
            file=sys.stderr,
        )
        return 2

    try:
        print_directory_tree(sys.argv[1])
    except OSError as error:
        print(f"{Fore.RED}Помилка: {error}{Style.RESET_ALL}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
