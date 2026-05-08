from dataclasses import dataclass, field
from typing import Optional


@dataclass
class MenuItem:
    code: str
    restaurant: str
    name: str
    description: str = ""
    free_text: bool = False


@dataclass
class RestaurantTemplate:
    name: str
    location: str = ""
    items: list[MenuItem] = field(default_factory=list)


@dataclass
class MenuTemplateStore:
    restaurants: list[RestaurantTemplate] = field(default_factory=list)


@dataclass
class TodayMenu:
    title: str
    selected_items: list[MenuItem] = field(default_factory=list)
    free_text_default_code: Optional[str] = None


@dataclass
class ParsedOrder:
    seq: int
    name: str
    code: str
    restaurant: str
    item_name: str
    note: str
    raw_line: str
    confidence: float
    warnings: list[str] = field(default_factory=list)


@dataclass
class UnresolvedLine:
    seq: Optional[int]
    raw_line: str
    reason: str
    suggestion: Optional[str] = None


@dataclass
class DuplicateOrder:
    name: str
    kept: ParsedOrder
    discarded: ParsedOrder


@dataclass
class ParseResult:
    orders: list[ParsedOrder] = field(default_factory=list)
    unresolved: list[UnresolvedLine] = field(default_factory=list)
    duplicates: list[DuplicateOrder] = field(default_factory=list)


@dataclass
class GroupedSummary:
    restaurant: str
    item_code: str
    item_name: str
    count: int
    orders: list[ParsedOrder] = field(default_factory=list)

