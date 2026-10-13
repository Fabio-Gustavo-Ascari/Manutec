from __future__ import annotations

from collections.abc import Callable

from assistencia_manager.domain.entities.access import AuditEntry


class AuditService:
    def __init__(self, unit_of_work_factory: Callable[[], object]):
        self._factory = unit_of_work_factory

    def record(self, *, user_id, action: str, module: str, entity_type: str | None = None, entity_id=None, details: str | None = None) -> AuditEntry:
        safe_details = " ".join((details or "").split())[:500] or None
        entry = AuditEntry(user_id, action.strip(), module.strip(), entity_type, entity_id, safe_details)
        with self._factory() as uow:
            uow.audit_logs.add(entry)
            uow.commit()
        return entry

    def list(self, *, module: str | None = None, action: str | None = None) -> tuple[AuditEntry, ...]:
        with self._factory() as uow:
            entries = tuple(uow.audit_logs.list())
        return tuple(item for item in entries if (not module or item.module == module) and (not action or item.action == action))
