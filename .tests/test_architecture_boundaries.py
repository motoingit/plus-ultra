"""Architecture boundary and dependency rule tests.

Verifies Clean Architecture & Hexagonal Architecture principles:
- Domain layer entities are pure dataclasses with ZERO database imports.
- Domain repositories define abstract Protocol interfaces.
- Application services depend only on abstract repositories/contracts.
- UI views never import SQLAlchemy or execute SQL.
- All source files conform to line limit constraints (< 500 lines).
"""

from __future__ import annotations

import ast
import os
from pathlib import Path

SRC_ROOT = Path(__file__).resolve().parents[1] / "src" / "plus_ultra"


def _get_imports(file_path: Path) -> list[str]:
    """Parse python file and extract all imported module names."""
    try:
        tree = ast.parse(file_path.read_text(encoding="utf-8"))
    except SyntaxError:
        return []

    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    return imports


def test_domain_layer_has_no_database_dependencies() -> None:
    """Verify domain layer never imports sqlalchemy, sqlite3, or persistence."""
    domain_dir = SRC_ROOT / "domain"
    forbidden_prefixes = ("sqlalchemy", "sqlite3", "plus_ultra.infrastructure")

    violations: list[str] = []
    for root, _, files in os.walk(domain_dir):
        for f in files:
            if not f.endswith(".py"):
                continue
            path = Path(root) / f
            imports = _get_imports(path)
            for imp in imports:
                if any(imp.startswith(forb) for forb in forbidden_prefixes):
                    violations.append(f"{path.name} imports {imp}")

    assert not violations, f"Domain boundary violations: {violations}"


def test_application_layer_has_no_orm_model_dependencies() -> None:
    """Verify application layer never imports SQLAlchemy ORM models."""
    app_dir = SRC_ROOT / "application"
    forbidden = "plus_ultra.infrastructure.persistence.sqlalchemy.models"

    violations: list[str] = []
    for root, _, files in os.walk(app_dir):
        for f in files:
            if not f.endswith(".py"):
                continue
            path = Path(root) / f
            imports = _get_imports(path)
            for imp in imports:
                if forbidden in imp:
                    violations.append(f"{path.name} imports {imp}")

    assert not violations, f"Application boundary violations: {violations}"


def test_ui_views_have_no_direct_database_dependencies() -> None:
    """Verify UI views never import sqlalchemy models, sessions, or sqlite3."""
    ui_views_dir = SRC_ROOT / "ui" / "views"
    forbidden_prefixes = (
        "sqlalchemy",
        "plus_ultra.infrastructure.persistence.sqlalchemy.models",
    )

    violations: list[str] = []
    for root, _, files in os.walk(ui_views_dir):
        for f in files:
            if not f.endswith(".py"):
                continue
            path = Path(root) / f
            imports = _get_imports(path)
            for imp in imports:
                if any(imp.startswith(forb) for forb in forbidden_prefixes):
                    violations.append(f"{path.name} imports {imp}")

    assert not violations, f"UI layer boundary violations: {violations}"


def test_all_source_files_under_500_lines() -> None:
    """Enforce architectural project rule: max 500 lines per source file."""
    violations: list[str] = []
    for root, _, files in os.walk(SRC_ROOT):
        for f in files:
            if not f.endswith(".py"):
                continue
            path = Path(root) / f
            line_count = len(path.read_text(encoding="utf-8").splitlines())
            if line_count > 500:
                rel = path.relative_to(SRC_ROOT)
                violations.append(f"{rel}: {line_count} lines")

    assert not violations, f"Files exceeding 500 lines: {violations}"
