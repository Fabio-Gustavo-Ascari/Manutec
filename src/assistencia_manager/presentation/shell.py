from __future__ import annotations

from PySide6.QtCore import Qt
from collections.abc import Iterable

from PySide6.QtWidgets import (
    QAbstractButton,
    QAbstractSpinBox,
    QComboBox,
    QCompleter,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

VISUAL_TOKENS = {
    "color.canvas": "#f4f7fb", "color.surface": "#ffffff", "color.ink": "#172033",
    "color.muted": "#667085", "color.border": "#e4e9f0", "color.primary": "#2563eb",
    "color.success": "#138a62", "color.warning": "#b7791f", "color.danger": "#c2414b",
    "radius.card": "14px", "radius.control": "8px", "space.page": "28px",
}

APP_STYLE = """
QMainWindow, QWidget { background: #f4f7fb; color: #172033; }
QWidget#sidebar { background: #172033; }
QListWidget#navigation { background: transparent; border: 0; color: #cbd5e1; outline: 0; }
QListWidget#navigation::item { padding: 9px 10px; border-radius: 7px; }
QListWidget#navigation::item:selected { background: #2563eb; color: white; }
QListWidget#navigation::item:focus { border: 1px solid #93c5fd; }
QListWidget#navigation::item[data-type="section"] { color: #94a3b8; padding: 15px 10px 5px; font-size: 11px; font-weight: 700; }
QFrame#appHeader { background: #ffffff; border-bottom: 1px solid #e4e9f0; }
QLabel#brandLabel { font-size: 16px; font-weight: 700; }
QLabel#contextLabel { color: #667085; }
QFrame#pageCard, QFrame#metricCard, QFrame#emptyState, QFrame#filterBar { background: #ffffff; border: 1px solid #e4e9f0; border-radius: 14px; }
QFrame#operationPanel, QFrame#checkoutPanel, QFrame#saleHeader { background: #ffffff; border: 1px solid #e4e9f0; border-radius: 10px; }
QFrame#checkoutPanel { background: #f8fafc; }
QFrame#metricCard[accent="primary"] { border-top: 3px solid #2563eb; }
QFrame#metricCard[accent="success"] { border-top: 3px solid #138a62; }
QFrame#metricCard[accent="warning"] { border-top: 3px solid #b7791f; }
QFrame#metricCard[accent="danger"] { border-top: 3px solid #c2414b; }
QLabel#pageTitle { font-size: 24px; font-weight: 700; }
QLabel#pageSubtitle, QLabel#metricCaption, QLabel#emptyDescription { color: #667085; }
QLabel#metricValue { font-size: 25px; font-weight: 700; }
QLabel#sectionTitle { font-size: 15px; font-weight: 700; }
QLabel#detailTitle { font-size: 17px; font-weight: 700; }
QLabel#statusPill { color: #2563eb; font-weight: 700; }
QLabel#salesTotal { background: #172033; color: white; border-radius: 10px; padding: 18px; font-size: 24px; font-weight: 700; }
QLabel#salesChange { color: #138a62; font-size: 16px; font-weight: 700; padding: 8px 0; }
QPushButton { min-height: 34px; padding: 0 13px; border: 1px solid #d8e0ea; border-radius: 8px; background: #ffffff; font-weight: 600; }
QPushButton:hover { background: #f1f5f9; }
QPushButton#primaryAction { background: #2563eb; border-color: #2563eb; color: white; }
QLineEdit, QComboBox, QSpinBox { min-height: 32px; border: 1px solid #cdd5e1; border-radius: 8px; padding: 0 8px; background: white; }
QPushButton:focus, QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QTableWidget:focus, QListWidget#navigation:focus { border: 2px solid #93c5fd; }
QPushButton:disabled { color: #98a2b3; background: #f2f4f7; }
QTableWidget { background: white; border: 1px solid #e4e9f0; border-radius: 8px; gridline-color: #edf0f5; selection-background-color: #dbeafe; selection-color: #172033; }
QHeaderView::section { background: #f8fafc; padding: 8px; border: 0; font-weight: 600; color: #475467; }
QStatusBar { background: #ffffff; border-top: 1px solid #e4e9f0; }
"""


def apply_accessibility(root: QWidget) -> None:
    """Apply shared keyboard and minimum-target rules to a page tree."""
    for control in root.findChildren(QWidget):
        if isinstance(control, QAbstractButton):
            if not control.accessibleName():
                control.setAccessibleName(control.text().strip() or "Ação")
            control.setMinimumHeight(max(control.minimumHeight(), 40))
            control.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        elif isinstance(control, QLineEdit):
            if not control.accessibleName():
                control.setAccessibleName(control.placeholderText() or "Campo de texto")
            control.setMinimumHeight(max(control.minimumHeight(), 40))
            control.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        elif isinstance(control, QComboBox):
            if not control.accessibleName():
                control.setAccessibleName("Campo de seleção")
            control.setMinimumHeight(max(control.minimumHeight(), 40))
            control.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        elif isinstance(control, QAbstractSpinBox):
            if not control.accessibleName():
                control.setAccessibleName("Campo numérico")
            control.setMinimumHeight(max(control.minimumHeight(), 40))
            control.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

class SearchableComboBox(QComboBox):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.setPlaceholderText("Digite para buscar...")
        self.setMaxVisibleItems(10)
        completer: QCompleter = self.completer()
        completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.setCurrentIndex(-1)

class PageShell(QFrame):
    def __init__(self, title: str, subtitle: str = "", parent: QWidget | None = None, *, actions: Iterable[QWidget] = ()) -> None:
        super().__init__(parent); self.setObjectName("pageCard")
        self.title_label = QLabel(title); self.title_label.setObjectName("pageTitle")
        self.subtitle_label = QLabel(subtitle); self.subtitle_label.setObjectName("pageSubtitle"); self.subtitle_label.setVisible(bool(subtitle))
        self.header_layout = QHBoxLayout(); heading = QVBoxLayout(); heading.setSpacing(3); heading.addWidget(self.title_label); heading.addWidget(self.subtitle_label); self.header_layout.addLayout(heading); self.header_layout.addStretch()
        for action in actions: self.header_layout.addWidget(action)
        self.body = QVBoxLayout(self); self.body.setContentsMargins(28, 22, 28, 28); self.body.setSpacing(16); self.body.addLayout(self.header_layout)


class DashboardMetricCard(QFrame):
    def __init__(self, caption: str, value: str = "—", detail: str = "", accent: str = "primary", parent: QWidget | None = None) -> None:
        super().__init__(parent); self.setObjectName("metricCard"); self.setProperty("accent", accent)
        self.caption_label = QLabel(caption); self.caption_label.setObjectName("metricCaption")
        self.value_label = QLabel(value); self.value_label.setObjectName("metricValue")
        self.detail_label = QLabel(detail); self.detail_label.setObjectName("metricCaption"); self.detail_label.setVisible(bool(detail))
        layout = QVBoxLayout(self); layout.setContentsMargins(18, 16, 18, 16); layout.setSpacing(5); layout.addWidget(self.caption_label); layout.addWidget(self.value_label); layout.addWidget(self.detail_label)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def set_value(self, value: str, detail: str = "") -> None:
        self.value_label.setText(value); self.detail_label.setText(detail); self.detail_label.setVisible(bool(detail))


class EmptyState(QFrame):
    def __init__(self, title: str, description: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent); self.setObjectName("emptyState")
        layout = QVBoxLayout(self); layout.setContentsMargins(24, 24, 24, 24); layout.setSpacing(6)
        title_label = QLabel(title); title_label.setObjectName("sectionTitle")
        description_label = QLabel(description); description_label.setObjectName("emptyDescription"); description_label.setWordWrap(True)
        layout.addWidget(title_label, alignment=Qt.AlignmentFlag.AlignHCenter); layout.addWidget(description_label, alignment=Qt.AlignmentFlag.AlignHCenter)


class FilterBar(QFrame):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent); self.setObjectName("filterBar"); self.layout = QHBoxLayout(self); self.layout.setContentsMargins(12, 10, 12, 10); self.layout.setSpacing(10)


class ActionBar(QFrame):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent); self.setObjectName("filterBar"); self.layout = QHBoxLayout(self); self.layout.setContentsMargins(12, 10, 12, 10); self.layout.setSpacing(10); self.layout.addStretch()


class AlertBanner(QFrame):
    def __init__(self, title: str, message: str, tone: str = "warning", parent: QWidget | None = None) -> None:
        super().__init__(parent); self.setObjectName("emptyState"); self.setProperty("tone", tone)
        layout = QVBoxLayout(self); layout.setContentsMargins(16, 12, 16, 12); layout.setSpacing(2)
        title_label = QLabel(title); title_label.setObjectName("sectionTitle")
        message_label = QLabel(message); message_label.setObjectName("emptyDescription"); message_label.setWordWrap(True)
        layout.addWidget(title_label); layout.addWidget(message_label)

def populate_combo(combo: QComboBox, items, label, identifier=lambda value: value.id) -> None:
    combo.blockSignals(True); combo.clear(); combo.setCurrentIndex(-1)
    for item in items: combo.addItem(label(item), identifier(item))
    combo.blockSignals(False); combo.setCurrentIndex(-1)
