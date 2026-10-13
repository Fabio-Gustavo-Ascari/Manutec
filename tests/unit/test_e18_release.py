from pathlib import Path

import pytest

from assistencia_manager.infrastructure.release import ReleaseGate


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_release_gate_accepts_a_coherent_final_release():
    report = ReleaseGate(PROJECT_ROOT).run()

    assert report.ok, report.failures
    assert report.version == "0.1.0"
    assert {check.name for check in report.checks} >= {
        "version-consistency",
        "migration-head",
        "bundled-build",
        "installer-data-safety",
        "support-package-privacy",
        "navigation-integration",
    }


def test_release_gate_reports_missing_release_contract(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "manutec"\nversion = "0.0.0"\n', encoding="utf-8"
    )

    report = ReleaseGate(tmp_path).run()

    assert not report.ok
    assert "version-consistency" in report.failures


@pytest.mark.parametrize("required_page", ["Relatórios", "Usuários e auditoria"])
def test_release_gate_requires_final_navigation_pages(required_page):
    report = ReleaseGate(PROJECT_ROOT).run()

    assert report.ok
    assert required_page in report.details["navigation-integration"]
