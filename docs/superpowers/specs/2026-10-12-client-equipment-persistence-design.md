# Persistência de Cliente e Equipamento — Design

## Objetivo

Conectar os casos de uso de Cliente e Equipamento ao banco SQLite por meio de
modelos SQLAlchemy, repositórios concretos, uma UoW integrada e uma nova
migração Alembic.

## Escopo

Esta etapa inclui:

- tabelas `clients` e `equipment`;
- conversão entre entidades de domínio e modelos ORM;
- criação, edição e consulta por identificador através dos repositórios;
- vínculo obrigatório de equipamento com cliente;
- commit e rollback pela `SqlAlchemyUnitOfWork`;
- testes de integração do fluxo persistente.

Busca textual, ordenação, paginação, inativação e telas permanecem fora desta
etapa.

## Modelo de dados

### `clients`

- `id`: UUID serializado como texto, chave primária;
- `status`: texto com `active` ou `inactive`;
- `name`: texto obrigatório;
- `contacts`: JSON com lista de textos;
- `document`, `address`, `notes`: textos opcionais.

### `equipment`

- `id`: UUID serializado como texto, chave primária;
- `status`: texto com `active` ou `inactive`;
- `client_id`: texto obrigatório, foreign key para `clients.id`;
- `equipment_type`: texto obrigatório;
- `brand`, `model`, `serial_number`: textos opcionais;
- `accessories`: JSON com lista de textos.

A exclusão em cascata não será habilitada nesta etapa; o domínio usa
inativação lógica e o relacionamento deve impedir equipamento órfão.

## Arquitetura

Os modelos ORM ficam em `infrastructure.database.models` e não serão expostos à
Application. Os repositórios recebem uma `Session`, implementam os contratos do
domínio e fazem a conversão explícita:

- `ClientRepositorySqlAlchemy` implementa `ClientRepository`;
- `EquipmentRepositorySqlAlchemy` implementa `EquipmentRepository`;
- `add` faz `session.add` de um modelo ORM;
- `get` busca por ID e retorna uma entidade de domínio ou `None`;
- `exists_by_name` e `exists_by_serial_number` usam consultas SQL simples.

A `SqlAlchemyUnitOfWork` criará os dois repositórios ao abrir a sessão. A
transação continuará sendo encerrada pelo contexto existente: commit no sucesso
e rollback quando uma exceção sair do bloco.

## Conversão e invariantes

- UUIDs serão convertidos por `EntityId.from_str` e `str(entity.id)`.
- Status será convertido entre `EntityStatus` e seu valor textual.
- Contatos e acessórios serão persistidos como listas JSON e reconstruídos como
  tuplas nas entidades.
- O repositório de equipamento não criará entidades sem `client_id`; a regra de
  cliente existente continuará sendo aplicada pelo serviço e reforçada pela
  foreign key do banco.
- A identidade e o status serão preservados em edições.

## Migração

Será criada a revisão `0002_client_equipment`, dependente de `0001_initial`,
criando as duas tabelas com índices/constraints necessários e removendo-as na
ordem inversa no downgrade.

## Testes

Os testes de integração usarão um SQLite temporário e provarão:

1. criação e leitura de cliente persistido;
2. criação e leitura de equipamento vinculado;
3. atualização preservando identidade e vínculo;
4. consulta de identificador ausente retornando `None`;
5. existência por nome e número de série;
6. rollback de uma operação que falha;
7. aplicação da migração em banco vazio e presença das tabelas.

A suíte atual e os testes unitários da Application devem continuar verdes.

## Critérios de aceite

- A UoW concreta expõe repositórios utilizáveis pelos serviços atuais.
- Nenhum modelo ORM ou import SQLAlchemy vaza para domínio ou Application.
- O banco impede equipamento sem cliente.
- O schema pode ser criado do zero via Alembic.
- Os fluxos persistentes têm cobertura de integração sem depender de mocks.
