# Manutec

Sistema desktop offline para gerenciamento de assistências técnicas.

O Manutec foi pensado para centralizar o atendimento da assistência em um único aplicativo Windows, com dados locais e funcionamento sem dependência de conexão constante com a internet.

## Objetivo

Organizar o trabalho diário de assistências técnicas, reunindo clientes, equipamentos, ordens de serviço, estoque, vendas, pagamentos e relatórios em uma experiência simples para pequenas empresas.

## Funcionalidades planejadas

- Cadastro de clientes e equipamentos.
- Ordens de serviço, orçamento e acompanhamento de status.
- Controle de estoque e movimentação de peças.
- Vendas e pagamentos.
- Dashboard e relatórios.
- Configurações da loja, backup e restauração.
- Aplicativo Windows com banco de dados local.

## Status atual

- [x] Fundação do domínio, configuração e banco SQLite.
- [x] Casos de uso de cadastrar, editar, consultar, listar e inativar clientes
  e equipamentos.
- [x] Persistência SQLAlchemy e migrações Alembic para clientes e equipamentos.
- [x] Busca textual e paginação na camada Application e nos repositórios.
- [x] Telas de cadastro, edição e validação de apresentação para clientes e equipamentos.
- [x] Busca e paginação disponíveis na camada de Application e persistência.
- [x] Busca e paginação integradas à interface desktop.
- [x] Ordens de serviço com ciclo de vida, orçamento, histórico, persistência e PDF.
- [x] Tela de ordens de serviço com abertura, filtros e transições críticas.

## Tecnologias

- Python 3.13.
- PySide6 para a interface desktop.
- SQLAlchemy e SQLite para persistência local.
- Alembic para migrações do banco.
- Pytest para testes automatizados.
- PyInstaller para empacotamento futuro.

## Desenvolvimento local

Requisitos:

- Windows com Python 3.13 disponível pelo launcher `py`;
- PowerShell;
- Git.

### Preparar o ambiente

Execute os comandos a partir da pasta do projeto:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Se o PowerShell bloquear a ativação do ambiente, permita scripts apenas para a
sessão atual:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### Executar testes

```powershell
python -m pytest
```

### Executar o aplicativo

```powershell
python -m assistencia_manager
```

### Banco de dados

O banco local é inicializado automaticamente ao executar a aplicação. Para
aplicar as migrações manualmente no banco definido em `alembic.ini`:

```powershell
python -m alembic upgrade head
```

Os dados da aplicação ficam em `%LOCALAPPDATA%\Manutec`, fora do diretório do
executável. Isso inclui o banco SQLite, logs e backups locais.

## Arquitetura

O código é organizado em camadas. A interface chama os casos de uso da
Application; as regras ficam no Domain; e a Infrastructure implementa os
contratos de persistência e fornece os adaptadores técnicos.

```text
Presentation
      │
      ▼
Application ───────► Domain
      │                  ▲
      │                  │ implementa contratos
      └────────────── Infrastructure
```

## Licença

Consulte as licenças das dependências antes da distribuição comercial.
