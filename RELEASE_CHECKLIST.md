# Checklist de release 0.1.0

- [ ] Executar `scripts\build-release.ps1 -Clean`.
- [ ] Compilar `installer\manutec.iss` com Inno Setup.
- [ ] Testar instalação limpa, atalho e inicialização.
- [ ] Testar atualização preservando `%LOCALAPPDATA%\Manutec`.
- [ ] Testar restauração de backup e rollback de arquivo inválido.
- [ ] Testar desinstalação sem apagar dados do usuário.
- [ ] Gerar pacote de suporte sanitizado.
- [ ] Autorizar publicação e assinatura, quando aplicável.
