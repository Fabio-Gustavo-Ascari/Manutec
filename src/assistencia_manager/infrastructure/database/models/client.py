from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from assistencia_manager.infrastructure.database.base import Base

if TYPE_CHECKING:
    from assistencia_manager.infrastructure.database.models.equipment import EquipmentModel


class ClientModel(Base):
    __tablename__ = "clients"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    contacts: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    document: Mapped[str | None] = mapped_column(String(50), nullable=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    equipment: Mapped[list[EquipmentModel]] = relationship(
        back_populates="client", cascade="save-update, merge"
    )
