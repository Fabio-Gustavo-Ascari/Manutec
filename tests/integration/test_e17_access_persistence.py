from assistencia_manager.application.services.access_service import AccessService
from assistencia_manager.application.services.audit_service import AuditService
from assistencia_manager.bootstrap import initialize_database
from assistencia_manager.domain.entities.access import Permission, UserRole
from assistencia_manager.infrastructure.config.paths import AppPaths
from assistencia_manager.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork


def test_users_permissions_and_audit_survive_database_round_trip(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    engine = initialize_database(AppPaths.default())
    factory = lambda: SqlAlchemyUnitOfWork(engine)
    access = AccessService(factory)
    audit = AuditService(factory)
    user = access.create_user("Operador", "operador", "P" * 12, UserRole.OPERATOR)
    access.set_permissions(user.id, {Permission("reports", "view")})
    audit.record(user_id=user.id, action="login", module="auth")
    restored = access.authenticate("operador", "P" * 12)
    assert restored.can(Permission("reports", "view"))
    assert audit.list(module="auth")[0].action == "login"
    engine.dispose()
