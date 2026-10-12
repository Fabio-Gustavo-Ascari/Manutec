# Assistência Manager — Fundação do Projeto

## Objetivo

Criar a base executável do Assistência Manager para Windows, com src-layout, PySide6, SQLite, SQLAlchemy, Alembic, ambiente virtual, testes isolados e uma janela principal navegável. Esta etapa não implementa regras de clientes, ordens de serviço, estoque ou vendas.

## Arquitetura

O projeto usa quatro camadas: Presentation, Application, Domain e Infrastructure. A Presentation depende de Application; Application depende de contratos do Domain e adaptadores de Infrastructure; Domain não depende de frameworks de interface ou persistência.

O banco é SQLite local, acessado exclusivamente por SQLAlchemy. O caminho persistente fica em `%LOCALAPPDATA%\\AssistenciaManager\\data`, fora do diretório do executável. A sessão é curta e transacional por operação.

## Escopo da etapa

- Configuração do projeto em `pyproject.toml`.
- Ambiente de desenvolvimento documentado.
- `AGENTS.md`, README, `.gitignore` e configuração do pytest.
- Engine SQLAlchemy e inicialização de SQLite.
- Configuração inicial do Alembic e migração-base.
- Janela PySide6 com menu lateral e páginas-placeholder.
- Testes de inicialização, persistência e reinicialização com banco temporário.

## Decisões de confiabilidade

- `PRAGMA foreign_keys=ON`, `journal_mode=WAL`, `busy_timeout` e `synchronous=FULL`.
- Migrações são versionadas pelo Alembic.
- Testes nunca apontam para o diretório de dados do usuário.
- O bootstrap cria os diretórios persistentes antes de abrir o banco.
- A interface não conhece SQLAlchemy.

## Critérios de aceite

1. O pacote instala em ambiente virtual com dependências fixadas.
2. `pytest` roda sem banco real.
3. A janela principal abre com navegação lateral em 1366x768.
4. O SQLite é criado em caminho persistente e sobrevive a reinicialização.
5. Há migração-base configurada.
6. A documentação explica criação do ambiente e execução.
7. Nenhum módulo comercial do MVP é implementado.

## Fora do escopo

Clientes, equipamentos, ordens de serviço, estoque, vendas, pagamentos, PDFs comerciais, backup/restauração, empacotamento final, instalador e atualização do produto.
