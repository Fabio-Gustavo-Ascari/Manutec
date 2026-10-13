# Cliente e Equipamento — Design da camada Application

## Objetivo

Adicionar os casos de uso de cadastro e edição de Cliente e Equipamento, com
contratos de persistência independentes de SQLAlchemy e testes unitários da
camada Application. A entrega deve preparar a integração concreta com o banco
sem incluir ainda telas, paginação, listagem ou migrações de negócio.

## Contexto e limites

O domínio já possui `Client`, `Equipment`, `EntityId`, exceções padronizadas,
contratos básicos de `Repository` e `UnitOfWork`, além da implementação inicial
de `SqlAlchemyUnitOfWork`. Os casos de uso serão a fronteira entre apresentação
e domínio; eles não conhecerão sessões, modelos ORM ou widgets.

Ficam fora desta fatia: consulta individual, listagem, paginação, inativação,
repositórios SQLAlchemy concretos, migrações das tabelas de negócio e telas.

## Arquitetura

### Contratos do domínio

Serão criados contratos específicos para `ClientRepository` e
`EquipmentRepository`, com operações mínimas para os casos de uso:

- `add(entity)` para novos registros;
- `get(identifier)` para edição;
- `exists_by_name(name)` para permitir a regra de duplicidade quando adotada
  pelo caso de uso;
- `remove(identifier)` permanece fora desta fatia, no contrato genérico já
  existente.

O `UnitOfWork` passará a expor `clients` e `equipment` como portas tipadas.
Implementações de teste em memória satisfarão esses contratos sem importar
frameworks.

### DTOs e serviços de Application

Cada operação terá DTO de entrada explícito e retorno com a entidade criada ou
atualizada:

- `CreateClient` recebe nome, contatos, documento, endereço e observações;
- `UpdateClient` recebe `EntityId` e os mesmos campos opcionais de alteração;
- `CreateEquipment` recebe `client_id`, tipo, marca, modelo, número de série e
  acessórios;
- `UpdateEquipment` recebe `EntityId` e os campos editáveis do equipamento.

Os serviços usam `with unit_of_work as uow`, carregam a entidade quando é uma
edição, levantam `EntityNotFoundError` quando necessário, validam o cliente do
equipamento por meio de `uow.clients.get`, chamam os métodos do domínio e
comitam somente ao final. Exceções deixam a UoW fazer rollback.

## Regras e erros

- As validações de conteúdo permanecem nas entidades do domínio.
- Cliente inexistente ao cadastrar equipamento produz `EntityNotFoundError`.
- Cliente ou equipamento inexistente ao editar produz
  `EntityNotFoundError`.
- O vínculo `Equipment.client_id` não pode ser alterado na edição desta fatia;
  uma futura operação específica tratará transferência de equipamento.
- Nenhuma entidade é persistida se a operação falhar antes do commit.

## Testes

Os testes unitários usarão uma UoW e repositórios em memória reais, não mocks do
comportamento da aplicação. Devem provar:

1. criação de cliente e equipamento;
2. edição preservando identidade;
3. rejeição de referências inexistentes;
4. rollback quando uma validação falha;
5. que os contratos da Application não importam SQLAlchemy.

A suíte completa existente deve permanecer verde.

## Critérios de aceite

- Os quatro casos de uso estão disponíveis por interfaces estáveis.
- Os casos de uso operam apenas sobre contratos do domínio.
- Os testes de Application falham antes da implementação e passam depois dela.
- O comportamento das entidades existentes não é alterado.
- A camada está pronta para receber repositórios SQLAlchemy em uma etapa
  posterior sem alterar os casos de uso.
