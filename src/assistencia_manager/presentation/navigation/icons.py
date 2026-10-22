"""Local vector icons shared by the sidebar and home shortcuts."""
from PySide6.QtCore import QByteArray, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer


_PATHS = {
    "Dashboard": '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>',
    "Ordens de serviço": '<rect x="5" y="4" width="14" height="17" rx="2"/><rect x="9" y="2" width="6" height="4" rx="1"/><path d="M9 11h6M9 15h6"/>',
    "Estoque": '<path d="m3 7 9-5 9 5v10l-9 5-9-5ZM3 7l9 5 9-5M12 12v10M7.5 4.5l9 5"/>',
    "Vendas": '<path d="M3 3h2l3 12h11l2-8H6"/><circle cx="9" cy="20" r="1"/><circle cx="18" cy="20" r="1"/>',
    "Financeiro": '<rect x="3" y="5" width="18" height="15" rx="2"/><path d="M3 9h18M16 14h5M6 5V3h12"/><circle cx="16" cy="14" r=".5"/>',
    "Clientes": '<circle cx="9" cy="7" r="4"/><path d="M2 21v-2a7 7 0 0 1 14 0v2M17 3a4 4 0 0 1 0 8M22 21v-2a7 7 0 0 0-4-6"/>',
    "Compras": '<path d="M4 7h16l1 14H3ZM8 7V5a4 4 0 0 1 8 0v2"/>',
    "Equipamentos": '<rect x="3" y="3" width="18" height="13" rx="2"/><path d="M8 21h8M12 16v5"/>',
    "Cadastros": '<path d="M3 7V4h7l2 3h9v14H3ZM8 14h8M12 10v8"/>',
    "Fiscal e periféricos": '<path d="M6 2h9l4 4v16l-3-2-4 2-3-2-3 2ZM14 2v5h5M9 11h6M9 15h6"/>',
    "Relatórios": '<path d="M4 3v18h17M8 16v-5M13 16V7M18 16v-3"/>',
    "Configurações": '<path d="M4 6h16M4 12h16M4 18h16"/><circle cx="9" cy="6" r="2"/><circle cx="16" cy="12" r="2"/><circle cx="8" cy="18" r="2"/>',
    "Usuários e auditoria": '<path d="m12 2 9 4v6c0 5-9 10-9 10S3 17 3 12V6ZM8 12l3 3 5-6"/>',
    "expanded": '<path d="m7 10 5 5 5-5"/>',
    "collapsed": '<path d="m10 7 5 5-5 5"/>',
}


def navigation_icon(title: str) -> QIcon:
    icon = QIcon()
    for mode, color in ((QIcon.Mode.Normal, "#2563eb"),
                        (QIcon.Mode.Selected, "#ffffff"),
                        (QIcon.Mode.Active, "#1d4ed8")):
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" '
               f'viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.7" '
               f'stroke-linecap="round" stroke-linejoin="round">{_PATHS[title]}</svg>')
        pixmap = QPixmap(48, 48)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        QSvgRenderer(QByteArray(svg.encode())).render(painter)
        painter.end()
        icon.addPixmap(pixmap, mode)
    return icon
