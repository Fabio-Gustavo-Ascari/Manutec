# Assistência Manager — instruções do projeto

## Arquitetura

O código usa as camadas Presentation, Application, Domain e Infrastructure. A interface PySide6 não acessa o banco diretamente. Regras de negócio pertencem ao Domain/Application; persistência pertence à Infrastructure.

## Ambiente

Use Python 3.13 em um ambiente virtual local:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

## Comandos

```powershell
pytest
python -m assistencia_manager
```

## Regras

- Não adicionar dependências sem justificar no plano da etapa.
- Não colocar regras de negócio em widgets.
- Não acessar o banco diretamente a partir da Presentation.
- Usar transações para operações críticas.
- Usar migrações Alembic para qualquer mudança de schema.
- Testes devem usar bancos temporários.
- Não registrar dados pessoais ou sensíveis em logs.
- Não apagar dados, backups ou arquivos do usuário sem confirmação explícita.

## Qualidade obrigatória

- Antes de concluir alterações, executar o `dev-harness` com o projeto específico.
- Tratar validações bloqueadas como pendências reais, nunca como aprovadas.
- Aplicar a skill `project-quality` quando disponível para análise de arquitetura, segurança, testes e evidências.
- Aplicar a skill `project-git` somente dentro deste repositório quando ele for criado; nunca operar o Git na pasta pai `Projetos`.
