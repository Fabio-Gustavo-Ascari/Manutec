from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

PAGE_DEFINITIONS: tuple[tuple[str, str], ...] = (
    ("Dashboard", "Indicadores gerenciais aparecerão aqui."),
    ("Clientes", "Cadastro e pesquisa de clientes."),
    ("Equipamentos", "Cadastro e pesquisa de equipamentos."),
    ("Ordens de serviço", "Abertura, orçamento e acompanhamento de status."),
    ("Estoque", "Cadastro de peças, saldos e movimentações."),
    ("Compras", "Pedidos, recebimentos e reposição de estoque."),
    ("Financeiro", "Contas a pagar, receber e fluxo de caixa."),
    ("Fiscal e periféricos", "NF-e, NFC-e, NFS-e, impressoras, leitor e PIX."),
    ("Vendas", "Vendas, recebimentos e caixa."),
    ("Cadastros", "Categorias, marcas, fornecedores, técnicos, serviços e garantias."),
    ("Configurações", "Configurações da assistência serão implementadas em etapa futura."),
    ("Relatórios", "Relatórios operacionais e gerenciais exportáveis."),
    ("Usuários e auditoria", "Usuários locais, permissões e histórico de alterações."),
)


class PlaceholderPage(QWidget):
    def __init__(self, title: str, description: str) -> None:
        super().__init__()
        title_label = QLabel(title)
        title_label.setObjectName("pageTitle")
        description_label = QLabel(description)
        description_label.setWordWrap(True)
        description_label.setObjectName("pageDescription")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 36, 40, 36)
        layout.addWidget(title_label)
        layout.addWidget(description_label)
        layout.addStretch()
