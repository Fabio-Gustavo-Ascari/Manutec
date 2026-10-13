from assistencia_manager.application.dto.inventory import CreatePartCommand, UpdatePartCommand
from assistencia_manager.application.services.inventory_service import InventoryService


class Repo:
    def __init__(self): self.data = {}
    def add(self, entity): self.data[entity.id] = entity
    def get(self, identifier): return self.data.get(identifier)
    def list(self): return tuple(self.data.values())
    def search(self, term, active_only, offset, limit): return self.list()[offset:offset + limit]
    def count(self, term, active_only): return len(self.data)
    def exists_by_sku(self, sku): return any(item.sku == sku for item in self.data.values())


class Uow:
    def __init__(self): self.parts = Repo()
    def __enter__(self): return self
    def __exit__(self, *args): pass


def test_catalog_updates_and_inactivates_part_without_deleting_it():
    uow = Uow()
    service = InventoryService(lambda: uow)
    part = service.create_part(CreatePartCommand("Cabo", "Acessórios"))
    updated = service.update(UpdatePartCommand(part.id, "Cabo USB", "Acessórios", "un", 2, 5, 1))
    inactive = service.deactivate(updated.id)

    assert inactive.name == "Cabo USB"
    assert service.get(part.id).status.value == "inactive"
