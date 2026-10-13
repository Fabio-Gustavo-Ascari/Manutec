# Cliente e Equipamento — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans (recommended) to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Implementar os casos de uso de cadastro e edição de Cliente e Equipamento sobre contratos de domínio independentes de SQLAlchemy.

**Architecture:** A camada Application receberá DTOs imutáveis e serviços pequenos que executam uma operação dentro de uma UnitOfWork. O domínio fornecerá contratos específicos para clientes e equipamentos; os testes usarão implementações em memória localizadas nos próprios testes, deixando a integração SQLAlchemy para uma etapa posterior.

**Tech Stack:** Python 3.13, dataclasses, typing.Protocol, pytest 9.1.1.

**Spec:** docs/superpowers/specs/2026-10-12-client-equipment-application-design.md

## Global Constraints

- Os casos de uso não importam SQLAlchemy, PySide6 ou infraestrutura.
- As validações de conteúdo permanecem nas entidades de domínio.
- A edição de equipamento preserva client_id.
- Exceções durante a operação devem provocar rollback pela UoW.
- A suíte existente deve permanecer verde.

## Review Focus

- Um equipamento criado com client_id inexistente deve falhar antes de ser adicionado.
- Uma edição de cliente ou equipamento inexistente deve produzir EntityNotFoundError e não fazer commit.
- Uma atualização com campo inválido deve preservar o estado armazenado após rollback.
- DTOs e serviços da Application não podem importar frameworks de infraestrutura.
- A identidade das entidades deve permanecer igual após edição.

### Task 1: Contratos tipados de repositórios e UoW

**Files:**
- Modify: src/assistencia_manager/domain/repositories.py
- Modify: src/assistencia_manager/domain/unit_of_work.py
- Test: tests/unit/test_application_contracts.py

**Interfaces:**
- Produces ClientRepository with add(Client), get(EntityId) -> Client | None, and exists_by_name(str) -> bool.
- Produces EquipmentRepository with add(Equipment), get(EntityId) -> Equipment | None, and exists_by_serial_number(str) -> bool.
- Produces UnitOfWork attributes clients: ClientRepository and equipment: EquipmentRepository.

- [ ] Step 1: Write the failing test

  Add tests that import the three contracts, assert their modules are in
  assistencia_manager.domain, and inspect that the UoW annotations expose
  clients and equipment.

- [ ] Step 2: Run test to verify it fails

  Run: .\.venv\Scripts\python.exe -m pytest tests/unit/test_application_contracts.py -q

  Expected: FAIL because the specific repository protocols and UoW attributes do not exist yet.

- [ ] Step 3: Implement the minimal contracts

  Add framework-free Protocol definitions and type the two attributes on the
  existing UnitOfWork; retain the generic Repository protocol for existing callers.

- [ ] Step 4: Run test to verify it passes

  Run: .\.venv\Scripts\python.exe -m pytest tests/unit/test_application_contracts.py -q

  Expected: PASS.

- [ ] Step 5: Commit

  git add src/assistencia_manager/domain/repositories.py src/assistencia_manager/domain/unit_of_work.py tests/unit/test_application_contracts.py
  git commit -m "feat: add typed client and equipment repository ports"

### Task 2: DTOs e serviços de cadastro

**Files:**
- Create: src/assistencia_manager/application/dto/client.py
- Create: src/assistencia_manager/application/dto/equipment.py
- Create: src/assistencia_manager/application/services/client_service.py
- Create: src/assistencia_manager/application/services/equipment_service.py
- Modify: src/assistencia_manager/application/dto/__init__.py
- Modify: src/assistencia_manager/application/services/__init__.py
- Test: tests/unit/test_application_services.py

**Interfaces:**
- Consumes ClientRepository, EquipmentRepository, and UnitOfWork from Task 1.
- Produces CreateClientCommand, UpdateClientCommand, CreateEquipmentCommand, and UpdateEquipmentCommand as frozen dataclasses.
- Produces ClientService.create(command) -> Client, ClientService.update(command) -> Client, EquipmentService.create(command) -> Equipment, and EquipmentService.update(command) -> Equipment.

- [ ] Step 1: Write the failing tests

  Add an in-memory UoW/repository fixture in the test module. Test that client
  creation adds and commits a Client; equipment creation requires an existing
  client; client update preserves identity; equipment update preserves both
  identity and client_id; missing entities raise EntityNotFoundError.

- [ ] Step 2: Run tests to verify they fail

  Run: .\.venv\Scripts\python.exe -m pytest tests/unit/test_application_services.py -q

  Expected: FAIL because the DTOs and service classes do not exist.

- [ ] Step 3: Implement the minimal DTOs and services

  Use frozen dataclasses with the entity fields. Services should use the UoW as
  a context manager, call repository get/add, validate the equipment client,
  call domain constructors or update, and rely on context-manager rollback for
  exceptions. Do not add list, query, deactivate, or duplicate policies.

- [ ] Step 4: Run focused tests

  Run: .\.venv\Scripts\python.exe -m pytest tests/unit/test_application_services.py -q

  Expected: PASS.

- [ ] Step 5: Run the full suite

  Run: .\.venv\Scripts\python.exe -m pytest -q

  Expected: all existing and new tests pass.

- [ ] Step 6: Commit

  git add src/assistencia_manager/application tests/unit/test_application_services.py
  git commit -m "feat: add client and equipment application services"

### Task 3: Boundary and rollback verification

**Files:**
- Modify: tests/unit/test_application_services.py
- Modify: tests/unit/test_domain_boundaries.py

**Interfaces:**
- Consumes the four services and DTOs from Task 2.
- Produces regression coverage for rollback, invalid updates, identity preservation, and absence of infrastructure imports.

- [ ] Step 1: Write the failing regression tests

  Add a test where an invalid client update raises DomainValidationError and
  the in-memory transaction does not retain the invalid mutation. Add a test
  that imports each Application module and asserts no imported module starts
  with sqlalchemy or PySide6.

- [ ] Step 2: Run tests to verify the new assertions fail

  Run: .\.venv\Scripts\python.exe -m pytest tests/unit/test_application_services.py tests/unit/test_domain_boundaries.py -q

  Expected: the rollback assertion fails until the in-memory UoW snapshots and
  restores repository state, or the service transaction behavior is corrected.

- [ ] Step 3: Implement the minimal test fixture correction

  Make only the test UoW transactionally faithful: snapshot stored entities on
  entry and restore them on rollback. Production code must remain unchanged if
  the services already rely correctly on the UoW protocol.

- [ ] Step 4: Run focused tests

  Run: .\.venv\Scripts\python.exe -m pytest tests/unit/test_application_services.py tests/unit/test_domain_boundaries.py -q

  Expected: PASS.

- [ ] Step 5: Run the complete verification

  Run: .\.venv\Scripts\python.exe -m pytest -q

  Expected: all tests pass with no warnings or errors.

- [ ] Step 6: Commit

  git add tests/unit/test_application_services.py tests/unit/test_domain_boundaries.py
  git commit -m "test: verify application transaction boundaries"
