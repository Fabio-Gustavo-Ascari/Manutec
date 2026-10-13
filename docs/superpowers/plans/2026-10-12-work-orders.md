# E03 — Ordens de serviço e orçamento Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implementar domínio, aplicação, persistência, PDF e interface do ciclo completo de ordens de serviço.

**Architecture:** A entidade `WorkOrder` controlará status, itens e totais no Domain. A Application orquestrará comandos e histórico através de `UnitOfWork`; Infrastructure fornecerá modelos, repositórios, migração e PDF; Presentation consumirá somente serviços.

**Tech Stack:** Python 3.13, dataclasses, SQLAlchemy 2, Alembic, SQLite, PySide6, ReportLab e Pytest.

**Spec:** `docs/superpowers/specs/2026-10-12-work-orders-design.md`

## Global Constraints

- A interface não acessa banco ou modelos de persistência diretamente.
- Ordem sempre referencia cliente e equipamento existentes.
- Status só muda por transições permitidas.
- Histórico não pode ser atualizado nem removido.
- Testes devem ser executados com o Python do `.venv`, `QT_QPA_PLATFORM=offscreen` e `--basetemp .pytest-tmp` quando necessário.

## Review Focus

- Tentativa de salto de status ou alteração após encerramento deve falhar com erro de domínio.
- Quantidades e valores monetários inválidos não podem produzir total incorreto.
- Histórico deve permanecer ordenado e imutável após novas alterações.
- Ordem com cliente/equipamento inexistente deve falhar antes do commit.
- PDF deve refletir os valores persistidos e os dados atuais da empresa.

### Task 1: Domain lifecycle and quotation

**Files:**
- Create: `src/assistencia_manager/domain/entities/work_order.py`
- Create: `src/assistencia_manager/domain/entities/work_order_history.py`
- Modify: `src/assistencia_manager/domain/entities/__init__.py`
- Test: `tests/unit/test_work_order_entity.py`

**Interfaces:** `WorkOrder.open(client_id, equipment_id, reported_issue, intake_checklist, notes)`; `WorkOrder.transition_to(status)`; `WorkOrder.add_item(...)`; `WorkOrder.total`; `WorkOrder.history`.

- [ ] Escrever testes para abertura, transições válidas e inválidas, itens, desconto, total e histórico.
- [ ] Executar os testes e confirmar falha por API ausente.
- [ ] Implementar enums, entidade, regras monetárias e eventos de histórico mínimos.
- [ ] Executar os testes unitários até passar.
- [ ] Executar compilação do pacote e revisar nomes públicos.

### Task 2: Application commands and contracts

**Files:**
- Create: `src/assistencia_manager/application/dto/work_order.py`
- Create: `src/assistencia_manager/application/services/work_order_service.py`
- Modify: `src/assistencia_manager/domain/repositories.py`
- Modify: `src/assistencia_manager/domain/unit_of_work.py`
- Test: `tests/unit/test_work_order_service.py`

- [ ] Escrever testes com UoW em memória para abrir, alterar orçamento, transicionar, consultar e pesquisar.
- [ ] Confirmar falhas esperadas.
- [ ] Implementar DTOs, contratos e serviço, incluindo validação de referências.
- [ ] Executar testes unitários até passar.

### Task 3: SQLAlchemy persistence and migration

**Files:**
- Create: `src/assistencia_manager/infrastructure/database/models/work_order.py`
- Create: `src/assistencia_manager/infrastructure/database/repositories/work_order.py`
- Create: `src/assistencia_manager/infrastructure/migrations/versions/0003_work_orders.py`
- Modify: model/repository exports and `SqlAlchemyUnitOfWork`
- Test: `tests/integration/test_work_order_persistence.py`

- [ ] Escrever teste de persistência round-trip, busca, histórico e rollback.
- [ ] Confirmar falha antes dos modelos/migração.
- [ ] Implementar modelos, conversões, repositório, UoW e migração.
- [ ] Executar integração com banco temporário e migração até passar.

### Task 4: PDF quotation and company metadata

**Files:**
- Create: `src/assistencia_manager/application/services/work_order_pdf.py`
- Modify: metadata DTO/repository only if required by existing contract
- Test: `tests/unit/test_work_order_pdf.py`

- [ ] Escrever teste que gera PDF em arquivo temporário e verifica presença dos dados essenciais.
- [ ] Confirmar falha pela ausência do serviço.
- [ ] Implementar geração determinística e segura com ReportLab.
- [ ] Executar teste e inspeção básica do PDF.

### Task 5: Presentation and end-to-end critical flows

**Files:**
- Create: `src/assistencia_manager/presentation/pages/work_orders.py`
- Modify: navigation, main window and page exports
- Test: `tests/unit/test_work_order_presentation.py`, `tests/integration/test_presentation_pages.py`

- [ ] Escrever testes para abertura, seleção, alteração de status, orçamento e cancelamento pela interface.
- [ ] Confirmar falha inicial.
- [ ] Implementar formulário, tabela, filtros, ações e mensagens usando o serviço de Application.
- [ ] Executar testes de apresentação em offscreen.

### Task 6: Full verification and documentation

**Files:** `README.md`, `Agents/index.md`, `Agents/activities/etapas.md` se presentes localmente.

- [ ] Rodar suíte completa, compilação, `git diff --check` e harness.
- [ ] Corrigir falhas com novo ciclo RED-GREEN.
- [ ] Atualizar status da E03 apenas se todos os critérios forem comprovados.
- [ ] Revisar diff e estado do Git; não fazer push sem autorização explícita.
