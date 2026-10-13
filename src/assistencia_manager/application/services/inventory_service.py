from __future__ import annotations

from collections.abc import Callable, Sequence

from assistencia_manager.application.dto.inventory import (
    CreatePartCommand, PartSearchQuery, RecordInventoryMovementCommand,
    ReservePartCommand, UpdatePartCommand,
)
from assistencia_manager.application.dto.pagination import Page
from assistencia_manager.domain.entities.inventory import (
    InventoryMovement, InventoryMovementType, Part, PartReservation, ReservationStatus, StockLedger,
)
from assistencia_manager.domain.exceptions import (
    DomainValidationError, DuplicateEntityError, EntityNotFoundError,
)
from assistencia_manager.domain.unit_of_work import UnitOfWork


class InventoryService:
    def __init__(self, unit_of_work_factory: Callable[[], UnitOfWork]) -> None:
        self._unit_of_work_factory = unit_of_work_factory

    def create_part(self, command: CreatePartCommand) -> Part:
        with self._unit_of_work_factory() as uow:
            if command.sku and uow.parts.exists_by_sku(command.sku.strip().upper()):
                raise DuplicateEntityError(f"SKU {command.sku} já cadastrado")
            part = Part.create(**command.__dict__) if hasattr(command, "__dict__") else Part.create(
                name=command.name, category=command.category, unit=command.unit, sku=command.sku,
                cost=command.cost, price=command.price, minimum_stock=command.minimum_stock,
                maximum_stock=command.maximum_stock,
                barcode=command.barcode, brand=command.brand, supplier_id=command.supplier_id,
                location=command.location, warranty_days=command.warranty_days, promotional_price=command.promotional_price,
            )
            uow.parts.add(part)
            return part

    def get(self, identifier):
        with self._unit_of_work_factory() as uow:
            part = uow.parts.get(identifier)
            if part is None:
                raise EntityNotFoundError(f"Peça {identifier} não encontrada")
            return part

    def update(self, command: UpdatePartCommand) -> Part:
        with self._unit_of_work_factory() as uow:
            part = self._get_part(uow, command.identifier)
            part.ensure_active()
            part.name = command.name.strip()
            part.category = command.category.strip()
            part.unit = command.unit.strip()
            replacement = Part.create(
                name=part.name, category=part.category, unit=part.unit, sku=part.sku,
                cost=command.cost, price=command.price, minimum_stock=command.minimum_stock,
                maximum_stock=command.maximum_stock,
                barcode=command.barcode, brand=command.brand, supplier_id=command.supplier_id,
                location=command.location, warranty_days=command.warranty_days, promotional_price=command.promotional_price,
            )
            replacement.id = part.id
            replacement.status = part.status
            uow.parts.add(replacement)
            return replacement

    def deactivate(self, identifier) -> Part:
        with self._unit_of_work_factory() as uow:
            part = self._get_part(uow, identifier)
            part.deactivate()
            uow.parts.add(part)
            return part

    def search(self, query: PartSearchQuery) -> Page[Part]:
        with self._unit_of_work_factory() as uow:
            offset = (query.page - 1) * query.page_size
            return Page(
                items=tuple(uow.parts.search(query.search, query.active_only, offset, query.page_size)),
                page=query.page, page_size=query.page_size,
                total_items=uow.parts.count(query.search, query.active_only),
            )

    def balance(self, identifier):
        with self._unit_of_work_factory() as uow:
            part = self._get_part(uow, identifier)
            ledger = StockLedger(tuple(uow.inventory_movements.list_for_part(part.id)))
            reservations = tuple(uow.reservations.list_for_part(part.id, active_only=True))
            return ledger.physical_balance(part.id), ledger.available_balance(part.id, reservations)

    def low_stock(self) -> Sequence[Part]:
        with self._unit_of_work_factory() as uow:
            result = []
            for part in uow.parts.list():
                physical = StockLedger(tuple(uow.inventory_movements.list_for_part(part.id))).physical_balance(part.id)
                if physical <= part.minimum_stock:
                    result.append(part)
            return tuple(result)

    def record_movement(self, command: RecordInventoryMovementCommand) -> InventoryMovement:
        with self._unit_of_work_factory() as uow:
            part = self._get_part(uow, command.part_id)
            part.ensure_active()
            movements = tuple(uow.inventory_movements.list_for_part(part.id))
            reservations = tuple(uow.reservations.list_for_part(part.id, active_only=True))
            ledger = StockLedger(movements)
            movement = ledger.record(
                part_id=part.id, movement_type=command.movement_type, quantity=command.quantity,
                reference_id=command.reference_id, note=command.note,
            )
            if ledger.available_balance(part.id, reservations) < 0:
                raise ValueError("Movimento reduziria o estoque disponível reservado")
            uow.inventory_movements.add(movement)
            return movement

    def reserve(self, command: ReservePartCommand) -> PartReservation:
        with self._unit_of_work_factory() as uow:
            part = self._get_part(uow, command.part_id)
            part.ensure_active()
            if uow.work_orders.get(command.work_order_id) is None:
                raise EntityNotFoundError(f"Ordem {command.work_order_id} não encontrada")
            ledger = StockLedger(tuple(uow.inventory_movements.list_for_part(part.id)))
            current = tuple(uow.reservations.list_for_part(part.id, active_only=True))
            reservation = PartReservation.reserve(
                part_id=part.id, work_order_id=command.work_order_id, quantity=command.quantity,
            )
            if ledger.available_balance(part.id, current + (reservation,)) < 0:
                raise ValueError("Estoque disponível insuficiente para reservar a peça")
            uow.reservations.add(reservation)
            return reservation

    def release_reservation(self, identifier) -> PartReservation:
        with self._unit_of_work_factory() as uow:
            reservation = self._get_reservation(uow, identifier)
            reservation.release()
            uow.reservations.add(reservation)
            return reservation

    def consume_reservation(self, identifier) -> PartReservation:
        with self._unit_of_work_factory() as uow:
            reservation = self._get_reservation(uow, identifier)
            part = self._get_part(uow, reservation.part_id)
            part.ensure_active()
            ledger = StockLedger(tuple(uow.inventory_movements.list_for_part(part.id)))
            movement = ledger.record(
                part_id=part.id,
                movement_type=InventoryMovementType.CONSUMPTION,
                quantity=reservation.quantity,
                reference_id=reservation.work_order_id,
            )
            reservation.consume()
            uow.inventory_movements.add(movement)
            uow.reservations.add(reservation)
            return reservation

    @staticmethod
    def _get_part(uow: UnitOfWork, identifier):
        part = uow.parts.get(identifier)
        if part is None:
            raise EntityNotFoundError(f"Peça {identifier} não encontrada")
        return part

    @staticmethod
    def _get_reservation(uow: UnitOfWork, identifier) -> PartReservation:
        reservation = uow.reservations.get(identifier)
        if reservation is None:
            raise EntityNotFoundError(f"Reserva {identifier} não encontrada")
        if reservation.status is not ReservationStatus.ACTIVE:
            raise DomainValidationError("Reserva não está ativa")
        return reservation
