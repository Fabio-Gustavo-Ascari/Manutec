# E04 — Estoque e peças

## Objetivo

Implementar o catálogo de produtos/peças e o controle de estoque do Manutec,
com saldos deriváveis exclusivamente de movimentos auditáveis, operações
críticas atômicas e integração segura com peças usadas em ordens de serviço.

## Entendimento validado

- A E03 continua responsável por ordens, orçamento e ciclo de vida.
- A E04 transforma peças do orçamento em itens reserváveis e consumíveis, sem
  permitir que a Presentation acesse banco ou modelos de persistência.
- O saldo físico nunca pode ficar negativo; o disponível também nunca pode
  ficar negativo quando há reservas.
- Movimentos são append-only. Correções são novos movimentos de ajuste,
  estorno ou devolução, nunca edição ou remoção do movimento original.
- Quantidades aceitam `Decimal` para unidades como unidade, metro e litro.
- Todas as operações que alteram estoque, reserva ou consumo ocorrem dentro de
  uma única transação da `UnitOfWork`.

## Catálogo de peças

Uma peça/produto possui identificador UUID, nome obrigatório, SKU opcional
único quando informado, categoria obrigatória, unidade de medida, custo,
preço, estoque mínimo e estado ativo/inativo. Custo, preço e estoque mínimo
usam `Decimal`; custo e preço são monetários com duas casas e quantidades são
positivas.

O catálogo oferece criação, edição dos dados descritivos, busca, paginação,
consulta de itens ativos/inativos e inativação. Inativar não apaga histórico,
movimentos, reservas nem consumos existentes; apenas impede novos usos em
operações futuras.

## Ledger e saldo

Cada movimento contém peça, tipo, quantidade positiva, custo/preço opcional,
referência externa opcional, observação, identificador e timestamp UTC. Os
tipos mínimos são:

- `ENTRY`: entrada de compra ou recebimento, soma ao saldo físico;
- `EXIT`: saída manual, subtrai do saldo físico;
- `ADJUSTMENT_IN` e `ADJUSTMENT_OUT`: ajustes de inventário auditáveis;
- `CONSUMPTION`: consumo vinculado a uma OS, subtrai do saldo físico;
- `RETURN`: devolução/estorno de consumo, soma ao saldo físico.

O saldo físico é a soma algébrica dos movimentos. Reserva não é movimento
físico: é um registro próprio vinculado à OS e à peça, com quantidade e estado.
O disponível é `saldo físico - reservas ativas`. Consultas de saldo devem
retornar ambos os valores e permitir reconstruir o saldo a partir do ledger.

## Integração com ordens de serviço

Ao aprovar uma OS, cada linha de orçamento de peça deve referenciar uma peça
ativa e pode ser reservada atomicamente. A reserva falha se o disponível for
insuficiente. A aprovação da OS e a criação das reservas pertencem à mesma
transação.

Ao iniciar a execução, as reservas da OS são convertidas em consumo: cada
conversão cria um movimento `CONSUMPTION` e encerra a reserva. A operação é
atômica e não pode consumir parcialmente.

Se a OS for reprovada ou cancelada antes do consumo, suas reservas são
liberadas. Depois do consumo, uma devolução cria movimento `RETURN` e não
altera o movimento original. A mesma reserva ou consumo não pode ser aplicado
duas vezes.

Para preservar compatibilidade com a E03, linhas antigas de peça sem
identificador de catálogo não podem ser reservadas automaticamente; a
aplicação deve exigir o vínculo antes da aprovação que movimenta estoque.

## Concorrência e atomicidade

As operações de reservar, consumir, liberar e devolver devem verificar o
estado atual dentro da transação e falhar sem alterações parciais. O banco
deve impor unicidade de SKU e referências de idempotência quando aplicável.
O serviço deve usar bloqueio/controle transacional compatível com SQLite e
testes concorrentes devem demonstrar que duas reservas não ultrapassam o
disponível.

## Presentation

A aplicação terá consultas e telas para cadastro de peças, saldo atual,
alertas de estoque mínimo, histórico de movimentos e ações de entrada, saída,
ajuste e estorno. A tela de OS exibirá o vínculo da peça e o estado da reserva
ou consumo, mas continuará chamando somente serviços da Application.

## Persistência

Serão criadas tabelas para produtos/peças, movimentos e reservas, com chaves
estrangeiras para produtos e, quando aplicável, ordens de serviço. O histórico
de movimentos não será sobrescrito nem removido por repositórios públicos.
Migrações devem preservar os dados existentes das migrações 0001–0003.

## Critérios de aceite

1. É possível cadastrar, consultar, pesquisar, paginar e inativar peças sem
   perder histórico.
2. Todo saldo físico pode ser reproduzido pela soma dos movimentos.
3. Entradas, saídas, ajustes, reservas, consumos, liberações e devoluções são
   validados no domínio e persistidos atomicamente.
4. Nenhuma operação permite saldo físico ou disponível negativo, inclusive sob
   concorrência.
5. Aprovação e execução de OS integram reservas e consumo sem baixa parcial.
6. Movimentos são auditáveis e não podem ser editados ou removidos.
7. Alertas de estoque mínimo, consultas e telas principais têm testes.
8. A suíte existente da E00–E03 permanece verde.
