from __future__ import annotations

from PySide6.QtWidgets import QComboBox, QFrame, QLabel, QVBoxLayout, QWidget

APP_STYLE = """
QMainWindow, QWidget { background: #f5f7fb; color: #172033; }
QFrame#pageCard { background: white; border: 1px solid #e1e6ef; border-radius: 10px; }
QLabel#pageTitle { font-size: 22px; font-weight: 700; }
QLabel#pageSubtitle { color: #667085; }
QPushButton { min-height: 32px; padding: 0 12px; border-radius: 6px; }
QPushButton#primaryAction { background: #2563eb; color: white; font-weight: 600; }
QLineEdit, QComboBox, QSpinBox { min-height: 30px; border: 1px solid #cdd5e1; border-radius: 5px; padding: 0 7px; background: white; }
QTableWidget { background: white; border: 1px solid #e1e6ef; gridline-color: #edf0f5; }
QHeaderView::section { background: #eef2f7; padding: 7px; border: 0; font-weight: 600; }
"""

class SearchableComboBox(QComboBox):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent); self.setEditable(True); self.setInsertPolicy(QComboBox.InsertPolicy.NoInsert); self.setPlaceholderText("Digite para buscar..."); self.setMaxVisibleItems(10); self.setCurrentIndex(-1)

class PageShell(QFrame):
    def __init__(self, title: str, subtitle: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent); self.setObjectName("pageCard")
        self.title_label = QLabel(title); self.title_label.setObjectName("pageTitle")
        self.subtitle_label = QLabel(subtitle); self.subtitle_label.setObjectName("pageSubtitle"); self.subtitle_label.setVisible(bool(subtitle))
        self.body = QVBoxLayout(self); self.body.setContentsMargins(24, 20, 24, 24); self.body.setSpacing(12); self.body.addWidget(self.title_label); self.body.addWidget(self.subtitle_label)

def populate_combo(combo: QComboBox, items, label, identifier=lambda value: value.id) -> None:
    combo.blockSignals(True); combo.clear(); combo.setCurrentIndex(-1)
    for item in items: combo.addItem(label(item), identifier(item))
    combo.blockSignals(False); combo.setCurrentIndex(-1)
