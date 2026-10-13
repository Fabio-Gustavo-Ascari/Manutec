from pathlib import Path


def test_domain_and_application_foundation_packages_exist():
    project_root = Path(__file__).parents[2]
    package_root = project_root / "src" / "assistencia_manager"

    expected = (
        package_root / "domain" / "entities",
        package_root / "domain" / "rules",
        package_root / "domain" / "exceptions",
        package_root / "application" / "services",
        package_root / "application" / "dto",
        package_root / "infrastructure" / "database" / "models",
        package_root / "infrastructure" / "database" / "repositories",
    )

    assert all(path.is_dir() for path in expected)


def test_domain_does_not_import_frameworks():
    project_root = Path(__file__).parents[2]
    domain_root = project_root / "src" / "assistencia_manager" / "domain"

    forbidden = ("PySide6", "sqlalchemy", "alembic")
    imports = "\n".join(path.read_text(encoding="utf-8") for path in domain_root.rglob("*.py"))

    assert not any(name.lower() in imports.lower() for name in forbidden)


def test_application_does_not_import_infrastructure_frameworks():
    project_root = Path(__file__).parents[2]
    application_root = project_root / "src" / "assistencia_manager" / "application"

    forbidden = ("PySide6", "sqlalchemy", "alembic")
    imports = "\n".join(
        path.read_text(encoding="utf-8") for path in application_root.rglob("*.py")
    )

    assert not any(name.lower() in imports.lower() for name in forbidden)
