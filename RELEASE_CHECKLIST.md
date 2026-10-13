# Checklist de release 0.1.0

- [x] Executar `scripts\build-release.ps1 -Clean`.
- [ ] Compilar `installer\manutec.iss` com Inno Setup.
- [x] Testar inicialização do executável e criação do banco em diretório temporário.
- [x] Validar atualização/desinstalação e preservação de dados por inspeção do contrato do instalador; teste físico depende do Inno Setup.
- [x] Testar restauração de backup e rollback de arquivo inválido.
- [x] Validar que a desinstalação não remove dados do usuário por inspeção do contrato; teste físico depende do Inno Setup.
- [x] Gerar/validar pacote de suporte sanitizado.
- [x] Homologar o padrão visual e a navegação das 13 telas em 1024×640.
- [x] Executar aceitação cliente → OS → estoque → venda → pagamento → caixa → financeiro → relatório.
- [x] Executar suíte completa, gate de release, sensores e harness oficial.
- [ ] Autorizar publicação e assinatura, quando aplicável.
