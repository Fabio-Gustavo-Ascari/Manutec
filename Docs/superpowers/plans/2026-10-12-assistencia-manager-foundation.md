# Assistência Manager Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Criar a fundação executável e testável do Assistência Manager.

**Architecture:** Aplicação PySide6 em camadas, com Application/Domain independentes da interface e Infrastructure responsável por SQLite/SQLAlchemy/Alembic.

**Tech Stack:** Python 3.13, PySide6 6.12.0, SQLAlchemy 2.0.52, Alembic 1.20.0, pytest 9.1.1, ReportLab 5.0.1 e PyInstaller 6.22.3.

**Spec:** `docs/superpowers/specs/2026-10-12-assistencia-manager-foundation-design.md`

## Global Constraints

- Não implementar clientes, equipamentos, ordens de serviço, estoque, vendas ou pagamentos.
- Dados persistentes ficam fora do diretório do executável, em `%LOCALAPPDATA%\\AssistenciaManager`.
- A interface não acessa SQLite/SQLAlchemy diretamente.
- Testes usam bancos temporários.
- Alterações de schema passam pelo Alembic.

## Review Focus

- Importar o pacote sem instalar a aplicação não deve criar banco nem diretórios.
- Criar o banco duas vezes deve ser idempotente.
- Um banco temporário deve sobreviver ao fechamento e reabertura da engine.
- Testes de UI não devem exigir display em ambiente headless.
- O caminho padrão deve funcionar quando `LOCALAPPDATA` não estiver definido.

### Task 1: Projeto, configuração e testes de persistência

**Files:** `pyproject.toml`, `pytest.ini`, `.gitignore`, `AGENTS.md`, `README.md`, `src/assistencia_manager/infrastructure/config/paths.py`, `src/assistencia_manager/infrastructure/database/engine.py`, `src/assistencia_manager/infrastructure/database/session.py`, `tests/integration/test_database_foundation.py`.

- Escrever testes para caminho persistente, criação idempotente, pragmas SQLite e persistência entre engines.
- Executar os testes e observar falha por módulos ausentes.
- Implementar configuração mínima e engine SQLAlchemy síncrona.
- Executar `pytest -q` e confirmar todos os testes verdes.

### Task 2: Bootstrap e migrações

**Files:** `alembic.ini`, `src/assistencia_manager/infrastructure/migrations/env.py`, `src/assistencia_manager/infrastructure/migrations/script.py.mako`, `src/assistencia_manager/infrastructure/migrations/versions/0001_initial.py`, `src/assistencia_manager/bootstrap.py`, `src/assistencia_manager/__main__.py`.

- Testar que o bootstrap cria diretórios e banco em caminho configurável.
- Implementar bootstrap e migração-base sem entidades comerciais.
- Executar testes e validação da configuração Alembic.

### Task 3: Janela principal e navegação

**Files:** `src/assistencia_manager/presentation/app.py`, `src/assistencia_manager/presentation/main_window.py`, `src/assistencia_manager/presentation/navigation/sidebar.py`, `src/assistencia_manager/presentation/pages/*.py`, `tests/unit/test_presentation_imports.py`.

- Testar imports e criação da janela em modo offscreen.
- Implementar menu lateral e páginas-placeholder.
- Executar suíte completa e validar inicialização.

### Task 4: Documentação e verificação final

**Files:** `docs/architecture.md`, `docs/installation.md`, `docs/usage.md`, `docs/licenses/THIRD_PARTY.md`, `scripts/dev.ps1`.

- Documentar comandos, arquitetura, escopo e licenças.
- Executar todos os testes e revisar os critérios de aceite.
