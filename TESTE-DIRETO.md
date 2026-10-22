# Teste direto do Manutec

O pacote portátil para Windows fica em `dist/Manutec/`. Para testar, abra
`dist/Manutec/Manutec.exe` mantendo a pasta `_internal` no mesmo diretório.

Na primeira execução, o aplicativo cria os dados em
`%LOCALAPPDATA%\Manutec`. O banco, logs e backups ficam fora da pasta do
executável, então atualizar o pacote não apaga os dados locais.

O fluxo recomendado para o primeiro teste é:

1. Abrir o Dashboard e testar os atalhos de Financeiro, Estoque, Ordens de
   serviço, Vendas, Clientes e Compras.
2. Cadastrar um cliente e um equipamento.
3. Abrir uma ordem de serviço e verificar o acompanhamento do status.
4. Cadastrar uma peça, movimentar o estoque e registrar uma venda.
5. Abrir Financeiro e Relatórios.
6. Em Configurações, gerar um backup antes de testar alterações ou restauração.

Este é um pacote de teste portátil. O instalador `.exe` ainda depende da
compilação com Inno Setup e a assinatura digital depende de um certificado de
publicação.
