import os

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("QT_QPA_PLATFORM") is None and os.environ.get("CI") == "true",
    reason="Qt UI test requires a configured display in CI",
)


def test_page_definitions_are_stable():
    from assistencia_manager.presentation.pages import PAGE_DEFINITIONS

    assert PAGE_DEFINITIONS[0][0] == "Dashboard"
    assert {title for title, _ in PAGE_DEFINITIONS} == {
        "Dashboard",
        "Clientes",
        "Equipamentos",
        "Ordens de serviço",
        "Estoque",
            "Compras",
        "Financeiro",
        "Vendas",
        "Configurações",
        "Cadastros",
    }
