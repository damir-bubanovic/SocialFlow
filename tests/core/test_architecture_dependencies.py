
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

            module_name = getattr(node, "module", None)

            if node.level == 0 and module_name:
                imports.add(module_name)

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


def test_posts_category_creation_uses_provider_contract() -> None:
    """Category creation must not import the WordPress provider."""
    paths = (
        SOURCE_ROOT
        / "modules"
        / "posts"
        / "controllers"
        / "wordpress_category_creation_controller.py",
        SOURCE_ROOT
        / "modules"
        / "posts"
        / "workers"
        / "wordpress_category_creation_worker.py",
    )

    forbidden = (
        "socialflow.modules.wordpress.adapters."
        "wordpress_category_provider"
    )

    for path in paths:
        assert forbidden not in _imports_from(path), (
            f"{path} imports the concrete WordPress category provider"
        )
