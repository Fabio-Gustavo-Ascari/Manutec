# Assistência Manager

Sistema desktop offline para gestão de assistências técnicas.

## Status

A Etapa 01 contém apenas a fundação do projeto: configuração, persistência técnica, migrações iniciais e navegação visual com páginas-placeholder. Os módulos comerciais ainda não foram implementados.

## Desenvolvimento

Requer Python 3.13 para o ambiente oficial:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
pytest
python -m assistencia_manager
```

Os dados da aplicação serão armazenados em `%LOCALAPPDATA%\\AssistenciaManager`, fora do diretório do executável.

## Validação pelo Harness

O projeto possui configuração em `.harness.yaml` e pode ser validado pelo harness global:

```powershell
..\dev-harness\harness.ps1 detect -Project .
..\dev-harness\harness.ps1 validate -Project . -Profile python
..\dev-harness\harness.ps1 report -Project ..\dev-harness
```

O estado atual da Fundação permanece pendente de validação completa enquanto o ambiente Python 3.13 e as dependências de desenvolvimento não estiverem disponíveis.
