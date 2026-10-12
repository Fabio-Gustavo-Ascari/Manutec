# Manutec

Sistema desktop offline para gerenciamento de assistências técnicas.

O Manutec foi pensado para centralizar o atendimento da assistência em um único aplicativo Windows, com dados locais e funcionamento sem dependência de conexão constante com a internet.

## Objetivo

Organizar o trabalho diário de assistências técnicas, reunindo clientes, equipamentos, ordens de serviço, estoque, vendas, pagamentos e relatórios em uma experiência simples para pequenas empresas.

## Funcionalidades planejadas

- Cadastro de clientes e equipamentos.
- Ordens de serviço, orçamento e acompanhamento de status.
- Controle de estoque e movimentação de peças.
- Vendas e pagamentos.
- Dashboard e relatórios.
- Configurações da loja, backup e restauração.
- Aplicativo Windows com banco de dados local.

## Tecnologias

- Python 3.13.
- PySide6 para a interface desktop.
- SQLAlchemy e SQLite para persistência local.
- Alembic para migrações do banco.
- Pytest para testes automatizados.
- PyInstaller para empacotamento futuro.

## Desenvolvimento local

Requer Python 3.13:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
pytest
python -m assistencia_manager
```

Os dados da aplicação serão armazenados em `%LOCALAPPDATA%\Manutec`, fora do diretório do executável.

## Arquitetura

O código é organizado em camadas para manter a interface, as regras de negócio e a persistência independentes:

```text
Presentation → Application → Domain
                    ↓
              Infrastructure
```

## Licença

Consulte as licenças das dependências antes da distribuição comercial.
