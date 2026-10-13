"""Deterministic release gate for the final offline Windows package."""

from __future__ import annotations

import argparse
import re
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ReleaseCheck:
    name: str
    passed: bool
    detail: str


@dataclass(frozen=True, slots=True)
class ReleaseReport:
    version: str | None
    checks: tuple[ReleaseCheck, ...]
    details: dict[str, str]

    @property
    def ok(self) -> bool:
        return all(check.passed for check in self.checks)

    @property
    def failures(self) -> tuple[str, ...]:
        return tuple(check.name for check in self.checks if not check.passed)


class ReleaseGate:
    """Checks release inputs without building, installing or deleting user data."""

    _VERSION_PATTERN = re.compile(r"(?<!\d)0\.\d+\.\d+(?!\d)")

    def __init__(self, project_root: Path) -> None:
        self.project_root = Path(project_root)

    def run(self) -> ReleaseReport:
        checks: list[ReleaseCheck] = []
        details: dict[str, str] = {}
        version = self._read_version()

        version_files = ("CHANGELOG.md", "RELEASE_NOTES.md", "RELEASE_CHECKLIST.md")
        version_ok = bool(version) and all(
            self._VERSION_PATTERN.search(self._read_text(name))
            and (version in self._read_text(name))
            for name in version_files
        )
        checks.append(ReleaseCheck("version-consistency", version_ok, version or "versão ausente"))

        migration_files = sorted(
            (self.project_root / "src" / "assistencia_manager" / "infrastructure" / "migrations" / "versions").glob("*.py")
        )
        migration_head = migration_files[-1].stem if migration_files else ""
        migration_ok = bool(migration_files) and "revision =" in migration_files[-1].read_text(encoding="utf-8")
        checks.append(ReleaseCheck("migration-head", migration_ok, migration_head))

        spec = self._read_text("packaging/manutec.spec")
        build_script = self._read_text("scripts/build-release.ps1")
        build_ok = all(
            token in spec for token in ("__main__.py", "infrastructure/migrations", "logging.config")
        ) and all(token in build_script for token in ("PyInstaller", "--clean", "--noconfirm"))
        checks.append(ReleaseCheck("bundled-build", build_ok, "PyInstaller onedir"))

        installer = self._read_text("installer/manutec.iss")
        uninstall_section = installer.split("[UninstallDelete]", 1)[-1]
        installer_ok = all(token in installer for token in ("{localappdata}\\Manutec\\data", "{localappdata}\\Manutec\\backups", "{localappdata}\\Manutec\\logs")) and "{localappdata}\\Manutec" not in uninstall_section
        checks.append(ReleaseCheck("installer-data-safety", installer_ok, "dados persistentes preservados"))

        support = self._read_text("scripts/create-support-package.ps1")
        support_ok = all(token in support for token in ("ConvertTo-Json", "Compress-Archive")) and not any(token in support for token in ("assistencia.db", "*.log"))
        checks.append(ReleaseCheck("support-package-privacy", support_ok, "sem banco ou logs brutos"))

        main_window = self._read_text("src/assistencia_manager/presentation/main_window.py")
        required_pages = ("Relatórios", "Usuários e auditoria")
        navigation = ", ".join(page for page in required_pages if page in main_window)
        navigation_ok = navigation == ", ".join(required_pages)
        details["navigation-integration"] = navigation
        checks.append(ReleaseCheck("navigation-integration", navigation_ok, navigation))

        return ReleaseReport(version, tuple(checks), details)

    def _read_version(self) -> str | None:
        try:
            with (self.project_root / "pyproject.toml").open("rb") as stream:
                return tomllib.load(stream)["project"]["version"]
        except (FileNotFoundError, KeyError, TypeError):
            return None

    def _read_text(self, relative_path: str) -> str:
        try:
            return (self.project_root / relative_path).read_text(encoding="utf-8")
        except FileNotFoundError:
            return ""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Valida os contratos da release final do Manutec")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    report = ReleaseGate(args.project_root).run()
    for check in report.checks:
        print(f"{'PASS' if check.passed else 'FAIL'} {check.name}: {check.detail}")
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
