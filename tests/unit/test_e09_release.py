from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_release_artifacts_define_reproducible_windows_build():
    spec = (PROJECT_ROOT / "packaging" / "manutec.spec").read_text(encoding="utf-8")
    build_script = (PROJECT_ROOT / "scripts" / "build-release.ps1").read_text(encoding="utf-8")

    assert "assistencia_manager" in spec and "__main__.py" in spec
    assert "infrastructure/migrations" in spec
    assert "logging.config" in spec
    assert "PyInstaller" in build_script
    assert "--clean" in build_script
    assert "--noconfirm" in build_script


def test_installer_preserves_user_data_on_uninstall():
    installer = (PROJECT_ROOT / "installer" / "manutec.iss").read_text(encoding="utf-8")

    assert "{localappdata}\\Manutec\\data" in installer
    assert "{localappdata}\\Manutec\\backups" in installer
    assert "{localappdata}\\Manutec\\logs" in installer
    assert "{app}" in installer
    assert "{localappdata}\\Manutec" not in installer.split("[UninstallDelete]", 1)[1]


def test_support_script_does_not_archive_database_or_raw_logs():
    support = (PROJECT_ROOT / "scripts" / "create-support-package.ps1").read_text(encoding="utf-8")

    assert "assistencia.db" not in support
    assert "*.log" not in support
    assert "ConvertTo-Json" in support
    assert "Compress-Archive" in support


def test_bootstrap_uses_migrations_bundled_next_to_the_application():
    bootstrap = (PROJECT_ROOT / "src" / "assistencia_manager" / "bootstrap.py").read_text(encoding="utf-8")

    assert "Config()" in bootstrap
    assert 'Path(__file__).parent / "infrastructure" / "migrations"' in bootstrap
    assert "parents[2] / \"alembic.ini\"" not in bootstrap
