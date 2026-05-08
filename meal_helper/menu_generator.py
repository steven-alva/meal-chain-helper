from collections import OrderedDict

from meal_helper.models import MenuItem, TodayMenu
from meal_helper.normalizer import normalize_code


def generate_group_message(today_menu: TodayMenu) -> str:
    lines = [today_menu.title.strip(), ""]

    for restaurant, items in _group_items_by_restaurant(today_menu.selected_items).items():
        display_name = _restaurant_display_name(restaurant, items)
        lines.append(display_name)
        for item in items:
            item_line = f"{normalize_code(item.code)}：{item.name}"
            if item.description:
                item_line += f"（{item.description}）"
            lines.append(item_line)
        lines.append("")

    lines.extend(["请大家接龙：", "1.", "2.", "3."])
    return "\n".join(lines).strip() + "\n"


def _group_items_by_restaurant(items: list[MenuItem]) -> OrderedDict[str, list[MenuItem]]:
    grouped: OrderedDict[str, list[MenuItem]] = OrderedDict()
    for item in items:
        grouped.setdefault(item.restaurant, []).append(item)
    return grouped


def _restaurant_display_name(restaurant: str, items: list[MenuItem]) -> str:
    if items and all(item.free_text for item in items):
        return f"特别节目（{restaurant}）"
    return restaurant

