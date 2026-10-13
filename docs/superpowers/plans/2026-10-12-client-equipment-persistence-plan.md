# Persistência de Cliente e Equipamento — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Persistir Cliente e Equipamento em SQLite via SQLAlchemy, mantendo os serviços da Application independentes da infraestrutura.

**Architecture:** Modelos ORM ficam na infraestrutura e repositórios adaptam-nos às entidades de domínio. A UoW cria os repositórios com a sessão aberta; Alembic cria as tabelas.

**Tech Stack:** Python 3.13, SQLAlchemy 2.0, Alembic, SQLite, pytest.

**Spec:** docs/superpowers/specs/2026-10-12-client-equipment-persistence-design.md

## Global Constraints

- Domínio e Application não importam SQLAlchemy.
- UUID é armazenado como texto.
- Contatos e acessórios são armazenados como JSON.
- Equipment.client_id é obrigatório e referencia clients.id.
- A suíte existente permanece verde.

### Task 1: Modelos ORM e migração

**Files:**
- Create: src/assistencia_manager/infrastructure/database/models/client.py
- Create: src/assistencia_manager/infrastructure/database/models/equipment.py
- Modify: src/assistencia_manager/infrastructure/database/models/__init__.py
- Create: src/assistencia_manager/infrastructure/migrations/versions/0002_client_equipment.py
- Test: tests/integration/test_business_schema.py

- [ ] Escrever testes falhando para tabelas, colunas, foreign key e aplicação da migração.
- [ ] Executar os testes e confirmar falha por modelos/revisão ausentes.
- [ ] Implementar modelos declarativos e migração reversível.
- [ ] Executar testes focados e confirmar sucesso.
- [ ] Commitar com `feat: add client and equipment persistence schema`.

### Task 2: Repositórios SQLAlchemy

**Files:**
- Create: src/assistencia_manager/infrastructure/database/repositories/client.py
- Create: src/assistencia_manager/infrastructure/database/repositories/equipment.py
- Modify: src/assistencia_manager/infrastructure/database/repositories/__init__.py
- Test: tests/integration/test_sqlalchemy_repositories.py

- [ ] Escrever testes falhando para add, get, exists e conversão ORM/domínio.
- [ ] Executar os testes e confirmar falha por repositórios ausentes.
- [ ] Implementar os adaptadores e conversões explícitas.
- [ ] Executar testes focados e confirmar sucesso.
- [ ] Commitar com `feat: implement client and equipment repositories`.

### Task 3: UoW concreta e integração

**Files:**
- Modify: src/assistencia_manager/infrastructure/database/unit_of_work.py
- Test: tests/integration/test_persistence_contracts.py

- [ ] Escrever teste falhando para a UoW expor clients e equipment e para commit/rollback.
- [ ] Executar o teste e confirmar falha.
- [ ] Instanciar os repositórios na entrada da UoW e manter o ciclo transacional atual.
- [ ] Executar a suíte completa.
- [ ] Commitar com `feat: integrate persistence repositories with unit of work`.
