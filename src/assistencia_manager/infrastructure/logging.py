from __future__ import annotations

import logging
import re

_SENSITIVE_FIELD_PATTERN = re.compile(
    r"(?i)\b(document|password|token|secret|authorization)\s*=\s*[^\s,;]+"
)


def sanitize_log_message(message: str) -> str:
    return _SENSITIVE_FIELD_PATTERN.sub(lambda match: f"{match.group(1)}=[REDACTED]", message)


class SanitizingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        try:
            rendered = record.getMessage()
        except Exception:
            rendered = str(record.msg)
        record.msg = sanitize_log_message(rendered)
        record.args = ()
        return True


def configure_logging(level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger("assistencia_manager")
    logger.setLevel(level.upper())
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.addFilter(SanitizingFilter())
        logger.addHandler(handler)
    logger.propagate = False
    return logger

