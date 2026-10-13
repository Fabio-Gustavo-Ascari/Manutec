# -*- mode: python ; coding: utf-8 -*-
"""Reproducible onedir build definition for the Windows Manutec release."""

from pathlib import Path

from PyInstaller.building.build_main import Analysis, COLLECT, EXE, PYZ


project_root = Path(SPECPATH).parent
migrations = project_root / "src" / "assistencia_manager" / "infrastructure" / "migrations"
hiddenimports = ["logging.config"]

a = Analysis(
    [str(project_root / "src" / "assistencia_manager" / "__main__.py")],
    pathex=[str(project_root / "src")],
    binaries=[],
    datas=[
        (str(migrations / "*.py"), "assistencia_manager/infrastructure/migrations"),
        (str(migrations / "versions" / "*.py"), "assistencia_manager/infrastructure/migrations/versions"),
    ],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="Manutec",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="Manutec",
)
