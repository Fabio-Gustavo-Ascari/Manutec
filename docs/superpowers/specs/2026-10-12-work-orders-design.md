# E03 — Ordens de serviço e orçamento

## Objetivo

Implementar o fluxo completo de uma ordem de serviço no Manutec, preservando as camadas existentes e garantindo que status, alterações relevantes e valores do orçamento sejam consistentes e auditáveis.

## Escopo aprovado

- Ordem vinculada obrigatoriamente a cliente e equipamento.
- Abertura com defeito relatado, checklist de entrada e observações.
- Diagnóstico e itens de orçamento: serviços e peças, quantidade, valor unitário e descrição.
- Desconto, subtotal e total calculados no domínio.
- Status: `ABERTA`, `EM_ANALISE`, `ORCAMENTO_ENVIADO`, `APROVADA`, `REPROVADA`, `EM_EXECUCAO`, `CONCLUIDA`, `ENTREGUE`, `CANCELADA`.
- Transições permitidas validadas pela entidade; saltos inválidos geram erro de domínio.
- Histórico imutável de abertura, alterações relevantes, mudança de status e cancelamento.
- Busca, filtros, paginação e telas desktop para os fluxos críticos.
- Geração de orçamento/comprovante PDF com dados da empresa configurados no `AppMetadata`.

## Fluxo de status

```text
ABERTA -> EM_ANALISE -> ORCAMENTO_ENVIADO -> APROVADA -> EM_EXECUCAO -> CONCLUIDA -> ENTREGUE
                                  └-------> REPROVADA
ABERTA, EM_ANALISE, ORCAMENTO_ENVIADO, APROVADA, EM_EXECUCAO -> CANCELADA
```

O orçamento pode ser atualizado enquanto a ordem estiver em `ABERTA`, `EM_ANALISE` ou `ORCAMENTO_ENVIADO`. Aprovação e execução exigem ordem válida; conclusão exige execução; entrega exige conclusão. Ordem entregue, reprovada ou cancelada não pode ser alterada.

## Decisões técnicas

- Valores monetários serão `Decimal`, persistidos como `Numeric(12, 2)` e normalizados para centavos na borda do domínio.
- Itens de peças não movimentam estoque nesta etapa; representam apenas linhas do orçamento.
- Histórico será append-only e exposto como sequência, sem operação de atualização ou remoção.
- PDF será gerado por um serviço de aplicação usando ReportLab e dados de empresa presentes no metadado da aplicação.
- A Presentation acessará somente serviços da Application, como nas telas de Clientes e Equipamentos.

## Critério de aceite

Uma ordem percorre somente transições permitidas, alterações relevantes mantêm histórico imutável e o orçamento/comprovante gerado contém dados consistentes com a ordem persistida.
