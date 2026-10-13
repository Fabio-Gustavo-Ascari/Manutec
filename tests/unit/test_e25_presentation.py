from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QComboBox, QLineEdit, QPushButton, QWidget

from assistencia_manager.presentation.main_window import MainWindow
from assistencia_manager.presentation.shell import apply_accessibility


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_accessibility_pass_sets_names_focus_and_touch_targets():
    _app()
    root = QWidget()
    button = QPushButton("Salvar", root)
    field = QLineEdit(root)
    field.setPlaceholderText("Nome")
    combo = QComboBox(root)
    apply_accessibility(root)

    assert button.accessibleName() == "Salvar"
    assert field.accessibleName() == "Nome"
    assert combo.accessibleName() == "Campo de seleção"
    assert button.minimumHeight() >= 40
    assert field.minimumHeight() >= 40
    assert combo.minimumHeight() >= 40
    assert button.focusPolicy() == Qt.FocusPolicy.StrongFocus
    assert field.focusPolicy() == Qt.FocusPolicy.StrongFocus
    root.close()


def test_accessibility_style_exposes_keyboard_focus_and_responsive_table_rules():
    from assistencia_manager.presentation.shell import APP_STYLE

    assert "QPushButton:focus" in APP_STYLE
    assert "QLineEdit:focus" in APP_STYLE
    assert "QTableWidget" in APP_STYLE
    assert "selection-background-color" in APP_STYLE


def test_main_window_keeps_supported_viewport_and_accessible_header_controls():
    _app()
    window = MainWindow()

    assert window.minimumSize().width() == 1024
    assert window.minimumSize().height() == 640
    assert window.help_button.minimumHeight() >= 40
    assert window.global_search.accessibleName() == "Buscar em qualquer tela..."
    assert window.sidebar.navigation.focusPolicy() == Qt.FocusPolicy.StrongFocus
    window.close()
