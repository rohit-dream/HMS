"""One-time scaffold helper — create domain folder tree."""

from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
DOMAINS = [
    "platform",
    "identity",
    "patients",
    "staff",
    "clinical",
    "billing",
    "laboratory",
    "pharmacy",
    "communications",
    "reporting",
    "audit",
]

EXTRA_DIRS = [
    "tests/unit/domains",
    "tests/integration/api/v1",
    "tests/fixtures",
    "worker/handlers",
    "worker/scheduler",
    "alembic/versions",
]


def main() -> None:
    base = BACKEND_ROOT / "app" / "domains"
    for domain in DOMAINS:
        (base / domain / "__init__.py").parent.mkdir(parents=True, exist_ok=True)
        init = base / domain / "__init__.py"
        if not init.exists():
            init.write_text('"""Domain module."""\n', encoding="utf-8")
        for sub in ("services", "repositories", "schemas"):
            folder = base / domain / sub
            folder.mkdir(parents=True, exist_ok=True)
            sub_init = folder / "__init__.py"
            if not sub_init.exists():
                sub_init.write_text('"""Domain package."""\n', encoding="utf-8")

    for relative in EXTRA_DIRS:
        (BACKEND_ROOT / relative).mkdir(parents=True, exist_ok=True)

    print("Scaffold directories created.")


if __name__ == "__main__":
    main()
