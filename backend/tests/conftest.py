from pathlib import Path

import pytest


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    tests_dir = Path(__file__).resolve().parent
    for item in items:
        level = item.path.relative_to(tests_dir).parts[0]
        if level in {"unit", "integration", "e2e"}:
            item.add_marker(getattr(pytest.mark, level))


@pytest.fixture(scope="session")
def examples_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "examples"
