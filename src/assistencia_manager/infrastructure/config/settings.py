from __future__ import annotations

import os
from dataclasses import dataclass

_SUPPORTED_LOG_LEVELS = frozenset({"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"})


@dataclass(frozen=True, slots=True)
class AppSettings:
    """Configuração não sensível derivada do ambiente local."""

    log_level: str = "INFO"

    @classmethod
    def from_environment(cls) -> AppSettings:
        configured_level = os.environ.get("MANUTEC_LOG_LEVEL", "INFO").upper()
        return cls(log_level=configured_level if configured_level in _SUPPORTED_LOG_LEVELS else "INFO")

