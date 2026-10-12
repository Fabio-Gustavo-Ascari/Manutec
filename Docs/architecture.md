# Arquitetura

O projeto é organizado em quatro camadas:

- `presentation`: PySide6 e interação com o usuário.
- `application`: casos de uso e serviços.
- `domain`: entidades e regras de negócio.
- `infrastructure`: SQLite, SQLAlchemy, Alembic, arquivos e integrações locais.

Dependências devem apontar para dentro. O domínio não importa PySide6, SQLAlchemy ou código específico do Windows.
