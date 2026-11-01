"""Architecture dependency regression tests."""

import ast
from pathlib import Path


SOURCE_ROOT = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "socialflow"
)


def _imports_from(path: Path) -> set[str]:
    """Return absolute module names imported by a Python file."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)

        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module:
                imports.add(node.module)

    return imports


def test_core_does_not_depend_on_feature_modules() -> None:
    """Core must remain independent of Accounts, Posts and WordPress."""
    core_root = SOURCE_ROOT / "core"

    for path in core_root.rglob("*.py"):
        for imported in _imports_from(path):
            assert not imported.startswith(
                "socialflow.modules."
            ), f"{path} imports feature module {imported}"


def test_accounts_does_not_depend_on_posts() -> None:
    """Accounts must not import Posts implementation modules."""
    accounts_root = SOURCE_ROOT / "modules" / "accounts"

    for path in accounts_root.rglob("*.py"):
        for imported in _imports_from(path):
            assert not (
                imported == "socialflow.modules.posts"
                or imported.startswith("socialflow.modules.posts.")
            ), f"{path} imports Posts module {imported}"


def test_shared_destination_has_one_canonical_definition() -> None:
    """PublishingDestination must be defined only in Core."""
    from socialflow.core.destination import PublishingDestination

    assert PublishingDestination.__module__ == "socialflow.core.destination"

    assert not (
        SOURCE_ROOT
        / "modules"
        / "posts"
        / "models"
        / "destination.py"
    ).exists()


def test_accounts_does_not_depend_on_wordpress() -> None:
    """Accounts must not import WordPress implementation modules."""
    accounts_root = SOURCE_ROOT / "modules" / "accounts"

    for path in accounts_root.rglob("*.py"):
        for imported in _imports_from(path):
            assert not (
                imported == "socialflow.modules.wordpress"
                or imported.startswith("socialflow.modules.wordpress.")
            ), f"{path} imports WordPress module {imported}"