from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

ItemT = TypeVar("ItemT")


@dataclass(frozen=True, slots=True)
class Page(Generic[ItemT]):
    items: tuple[ItemT, ...]
    page: int
    page_size: int
    total_items: int

    @property
    def total_pages(self) -> int:
        return (self.total_items + self.page_size - 1) // self.page_size
