# Instalação de desenvolvimento

1. Instale Python 3.13 para Windows.
2. Abra PowerShell na pasta do projeto.
3. Crie e ative o ambiente virtual:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

4. Instale as dependências:

```powershell
python -m pip install -e ".[dev]"
```

5. Execute os testes com `pytest`.

O instalador comercial Inno Setup e o pacote PyInstaller ainda não fazem parte desta etapa.
