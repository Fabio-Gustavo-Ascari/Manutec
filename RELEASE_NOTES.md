# Manutec 0.1.0

Versão inicial para Windows 10/11 x64. O instalador mantém os dados em
`%LOCALAPPDATA%\Manutec` durante atualização e desinstalação.

Antes de atualizar, gere um backup pela tela de Configurações. Para suporte,
execute `scripts\create-support-package.ps1`; o pacote gerado não inclui banco,
backups nem conteúdo bruto de logs.

A interface final foi homologada em todas as 13 telas no viewport mínimo de
1024×640. Conteúdos maiores que a área útil permanecem acessíveis por rolagem
horizontal e vertical sob demanda. O fluxo integrado de cliente, ordem de
serviço, estoque, venda, pagamento, caixa, financeiro e relatório foi validado
com SQLite e migrações reais.
