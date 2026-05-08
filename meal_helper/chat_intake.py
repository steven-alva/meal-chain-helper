from dataclasses import dataclass

from meal_helper.history_parser import extract_menu_templates
from meal_helper.models import MenuItem, MenuTemplateStore, TodayMenu


@dataclass
class ParseMenuContext:
    menu: TodayMenu
    source: str
    note: str
    extracted_store: MenuTemplateStore


def build_menu_context_from_chat(
    raw_text: str, fallback_menu: TodayMenu | None = None
) -> ParseMenuContext:
    extracted_store = _drop_empty_restaurants(extract_menu_templates(raw_text))
    extracted_items = _flatten_store_items(extracted_store)
    if extracted_items:
        return ParseMenuContext(
            menu=_today_menu_from_items(extracted_items),
            source="chat",
            note=(
                f"已从聊天记录识别 {len(extracted_store.restaurants)} 家餐厅、"
                f"{len(extracted_items)} 个菜品，并按这些编码整理。"
            ),
            extracted_store=extracted_store,
        )

    if fallback_menu and fallback_menu.selected_items:
        return ParseMenuContext(
            menu=fallback_menu,
            source="selected",
            note=f"未在聊天记录里识别到菜单，已使用下方已选的 {len(fallback_menu.selected_items)} 个菜品整理。",
            extracted_store=MenuTemplateStore(),
        )

    return ParseMenuContext(
        menu=TodayMenu(title=""),
        source="loose",
        note="未在聊天记录里识别到菜单，先按接龙里的编号生成临时清单。",
        extracted_store=MenuTemplateStore(),
    )


def _today_menu_from_items(items: list[MenuItem]) -> TodayMenu:
    free_text_codes = [item.code for item in items if item.free_text]
    return TodayMenu(
        title="",
        selected_items=items,
        free_text_default_code=free_text_codes[0] if free_text_codes else None,
    )


def _flatten_store_items(store: MenuTemplateStore) -> list[MenuItem]:
    return [item for restaurant in store.restaurants for item in restaurant.items]


def _drop_empty_restaurants(store: MenuTemplateStore) -> MenuTemplateStore:
    return MenuTemplateStore(
        restaurants=[restaurant for restaurant in store.restaurants if restaurant.items]
    )
