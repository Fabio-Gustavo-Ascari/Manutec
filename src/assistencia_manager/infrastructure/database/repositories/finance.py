from sqlalchemy import select
from assistencia_manager.domain.entities.finance import Commission, FinancialEntry, FinancialEntryStatus, FinancialEntryType, RecurringExpense
from assistencia_manager.domain.identifiers import EntityId
from assistencia_manager.infrastructure.database.models.finance import CommissionModel, FinancialEntryModel, RecurringExpenseModel


class SqlAlchemyFinancialEntryRepository:
    def __init__(self, session): self._session = session
    def add(self, entity):
        self._session.merge(FinancialEntryModel(id=str(entity.id), entry_type=entity.entry_type.value, description=entity.description, amount=entity.amount, due_date=entity.due_date, category=entity.category, cost_center=entity.cost_center, source_type=entity.source_type, source_id=str(entity.source_id) if entity.source_id else None, paid_amount=entity.paid_amount, paid_date=entity.paid_date, status=entity.status.value, created_at=entity.created_at))
    def get(self, identifier):
        model = self._session.get(FinancialEntryModel, str(identifier))
        return self._to_entity(model) if model else None
    def list(self): return tuple(self._to_entity(model) for model in self._session.scalars(select(FinancialEntryModel).order_by(FinancialEntryModel.due_date)))
    def remove(self, identifier): raise NotImplementedError("Lançamentos financeiros não são removidos")
    def list_by_period(self, start, end): return tuple(item for item in self.list() if start <= item.due_date <= end)
    @staticmethod
    def _to_entity(model):
        return FinancialEntry(FinancialEntryType(model.entry_type), model.description, model.amount, model.due_date, model.category, model.cost_center, model.source_type, EntityId.from_str(model.source_id) if model.source_id else None, model.paid_amount, model.paid_date, FinancialEntryStatus(model.status), EntityId.from_str(model.id), model.created_at)


class SqlAlchemyRecurringExpenseRepository:
    def __init__(self, session): self._session = session
    def add(self, entity): self._session.merge(RecurringExpenseModel(id=str(entity.id), description=entity.description, amount=entity.amount, due_day=entity.due_day, category=entity.category, cost_center=entity.cost_center, active=entity.active))
    def get(self, identifier):
        model = self._session.get(RecurringExpenseModel, str(identifier))
        return RecurringExpense(model.description, model.amount, model.due_day, model.category, model.cost_center, model.active, EntityId.from_str(model.id)) if model else None
    def list(self): return tuple(self.get(model.id) for model in self._session.scalars(select(RecurringExpenseModel)))
    def remove(self, identifier): raise NotImplementedError("Recorrências são inativadas")


class SqlAlchemyCommissionRepository:
    def __init__(self, session): self._session = session
    def add(self, entity): self._session.merge(CommissionModel(id=str(entity.id), seller_id=str(entity.seller_id), sale_id=str(entity.sale_id), base_amount=entity.base_amount, percentage=entity.percentage, amount=entity.amount))
    def get(self, identifier):
        model = self._session.get(CommissionModel, str(identifier))
        return Commission(EntityId.from_str(model.seller_id), EntityId.from_str(model.sale_id), model.base_amount, model.percentage, EntityId.from_str(model.id)) if model else None
    def list(self): return tuple(self.get(model.id) for model in self._session.scalars(select(CommissionModel)))
    def remove(self, identifier): raise NotImplementedError("Comissões são imutáveis")
