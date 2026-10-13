from sqlalchemy import select
from assistencia_manager.domain.entities.access import AuditEntry, User, UserRole
from assistencia_manager.domain.identifiers import EntityId
from assistencia_manager.infrastructure.database.models.access import UserModel, AuditLogModel

class SqlAlchemyUserRepository:
    def __init__(self, session): self._session = session
    def add(self, entity):
        self._session.merge(UserModel(id=str(entity.id), display_name=entity.display_name, username=entity.username, role=entity.role.value, permissions=",".join(sorted(entity.permissions)), password_hash=entity.password_hash, active=entity.active, created_at=entity.created_at))
    def get(self, identifier):
        model = self._session.get(UserModel, str(identifier)); return self._to_entity(model) if model else None
    def get_by_username(self, username):
        model = self._session.scalar(select(UserModel).where(UserModel.username == username)); return self._to_entity(model) if model else None
    def list(self): return tuple(self._to_entity(model) for model in self._session.scalars(select(UserModel).order_by(UserModel.username)))
    def remove(self, identifier): raise NotImplementedError("Usuários são inativados")
    @staticmethod
    def _to_entity(model):
        return User(model.display_name, model.username, UserRole(model.role), frozenset(filter(None, (model.permissions or "").split(","))), model.active, model.password_hash, EntityId.from_str(model.id), model.created_at)

class SqlAlchemyAuditRepository:
    def __init__(self, session): self._session = session
    def add(self, entity):
        self._session.add(AuditLogModel(id=str(entity.id), user_id=str(entity.user_id) if entity.user_id else None, action=entity.action, module=entity.module, entity_type=entity.entity_type, entity_id=str(entity.entity_id) if entity.entity_id else None, details=entity.details, created_at=entity.created_at))
    def get(self, identifier):
        model = self._session.get(AuditLogModel, str(identifier)); return self._to_entity(model) if model else None
    def list(self): return tuple(self._to_entity(model) for model in self._session.scalars(select(AuditLogModel).order_by(AuditLogModel.created_at, AuditLogModel.id)))
    def remove(self, identifier): raise NotImplementedError("Auditoria é append-only")
    @staticmethod
    def _to_entity(model):
        return AuditEntry(EntityId.from_str(model.user_id) if model.user_id else None, model.action, model.module, model.entity_type, EntityId.from_str(model.entity_id) if model.entity_id else None, model.details, model.created_at, EntityId.from_str(model.id))
