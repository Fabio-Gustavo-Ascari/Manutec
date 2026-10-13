from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from assistencia_manager.domain.exceptions import DomainValidationError
from assistencia_manager.domain.identifiers import EntityId


class UserRole(Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    OPERATOR = "operator"
    VIEWER = "viewer"


@dataclass(frozen=True, slots=True)
class Permission:
    module: str
    action: str

    def __post_init__(self):
        if not self.module.strip() or not self.action.strip():
            raise DomainValidationError("Permissão inválida")

    @property
    def key(self) -> str:
        return f"{self.module.strip().lower()}:{self.action.strip().lower()}"


def _hash_password(credential: str, salt: bytes | None = None) -> str:
    if not isinstance(credential, str) or len(credential) < 8:
        raise DomainValidationError("Senha deve possuir pelo menos 8 caracteres")
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", credential.encode(), salt, 120_000)
    return f"pbkdf2_sha256$120000${salt.hex()}${digest.hex()}"


@dataclass(slots=True)
class User:
    display_name: str
    username: str
    role: UserRole = UserRole.OPERATOR
    permissions: frozenset[str] = frozenset()
    active: bool = True
    password_hash: str = ""
    id: EntityId = field(default_factory=EntityId.new)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def create(cls, display_name: str, username: str, credential: str, role: UserRole = UserRole.OPERATOR):
        name, login = display_name.strip(), username.strip().lower()
        if not name or not login or any(ch.isspace() for ch in login):
            raise DomainValidationError("Nome e usuário são obrigatórios")
        return cls(name, login, role, frozenset(), True, _hash_password(credential))

    def verify_password(self, credential: str) -> bool:
        if not self.active or not self.password_hash.startswith("pbkdf2_sha256$"):
            return False
        _, rounds, salt_hex, expected = self.password_hash.split("$", 3)
        actual = hashlib.pbkdf2_hmac("sha256", credential.encode(), bytes.fromhex(salt_hex), int(rounds)).hex()
        return hmac.compare_digest(actual, expected)

    def set_permissions(self, permissions: set[Permission] | frozenset[Permission]) -> None:
        self.permissions = frozenset(item.key for item in permissions)

    def can(self, permission: Permission) -> bool:
        return self.role is UserRole.ADMIN or permission.key in self.permissions or f"{permission.module}:*" in self.permissions


@dataclass(frozen=True, slots=True)
class AuditEntry:
    user_id: EntityId | None
    action: str
    module: str
    entity_type: str | None = None
    entity_id: EntityId | None = None
    details: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    id: EntityId = field(default_factory=EntityId.new)
