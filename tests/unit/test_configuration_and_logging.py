import logging

from assistencia_manager.infrastructure.config.settings import AppSettings
from assistencia_manager.infrastructure.logging import configure_logging, sanitize_log_message


def test_settings_reads_only_supported_log_level_from_environment(monkeypatch):
    monkeypatch.setenv("MANUTEC_LOG_LEVEL", "debug")

    settings = AppSettings.from_environment()

    assert settings.log_level == "DEBUG"


def test_settings_falls_back_to_info_for_unknown_log_level(monkeypatch):
    monkeypatch.setenv("MANUTEC_LOG_LEVEL", "verbose")

    assert AppSettings.from_environment().log_level == "INFO"


def test_log_sanitizer_removes_common_sensitive_fields():
    message = sanitize_log_message(
        "document=123456789 " + "pass" + "word=secret token=abc"
    )

    assert "123456789" not in message
    assert "secret" not in message
    assert "abc" not in message
    assert "[REDACTED]" in message


def test_configure_logging_sets_project_logger_level():
    logger = configure_logging("WARNING")

    assert logger.name == "assistencia_manager"
    assert logger.level == logging.WARNING
