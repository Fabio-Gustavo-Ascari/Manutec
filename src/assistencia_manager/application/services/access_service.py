from __future__ import annotations

from collections.abc import Callable

from assistencia_manager.domain.entities.access import Permission, User, UserRole
from assistencia_manager.domain.exceptions import DomainValidationError


class AccessService:
    def __init__(self, unit_of_work_factory: Callable[[], object], audit_service=None):
        self._factory = unit_of_work_factory
        self._audit_service = audit_service

    def _audit(self, **values):
        if self._audit_service is not None:
            self._audit_service.record(**values)

    def create_user(self, display_name: str, username: str, credential: str | None = None, role: UserRole = UserRole.OPERATOR, **kwargs) -> User:
        credential = credential if credential is not None else kwargs.get("password")
        with self._factory() as uow:
            if uow.users.get_by_username(username.strip().lower()):
                raise DomainValidationError("Usuário já cadastrado")
            user = User.create(display_name, username, credential, role)
            uow.users.add(user)
            uow.commit()
            self._audit(user_id=user.id, action="user_created", module="users")
            return user

    def authenticate(self, username: str, credential: str | None = None, **kwargs) -> User:
        credential = credential if credential is not None else kwargs.get("password")
        with self._factory() as uow:
            user = uow.users.get_by_username(username.strip().lower())
            if user is None or not user.verify_password(credential):
                self._audit(user_id=user.id if user else None, action="login_failed", module="auth")
                raise DomainValidationError("Usuário ou senha inválidos")
            self._audit(user_id=user.id, action="login", module="auth")
            return user

    def set_permissions(self, user_id, permissions: set[Permission]) -> User:
        with self._factory() as uow:
            user = uow.users.get(user_id)
            if user is None:
                raise DomainValidationError("Usuário não encontrado")
            user.set_permissions(permissions)
            uow.users.add(user)
            uow.commit()
            return user

    def can(self, user: User, permission: Permission) -> bool:
        return user.can(permission)

    def list_users(self) -> tuple[User, ...]:
        with self._factory() as uow:
            return tuple(uow.users.list())
