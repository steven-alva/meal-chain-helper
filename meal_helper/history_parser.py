import re
import unicodedata

from meal_helper.models import MenuItem, MenuTemplateStore, RestaurantTemplate
from meal_helper.normalizer import normalize_code


MENU_ITEM_RE = re.compile(r"^\s*([A-Za-z])\s*(?:[:：]|[.．、\)）])\s*(.+?)\s*$")
ORDER_LINE_RE = re.compile(r"^\s*\d+[\.\、\)\）]\s*.+$")
PARENS_RE = re.compile(r"^(.+?)[（(](.*)[）)]\s*$")

FREE_TEXT_KEYWORDS = ("自选", "自定义", "自由")


def extract_menu_templates(raw_text: str) -> MenuTemplateStore:
    restaurants: list[RestaurantTemplate] = []
    restaurant_by_name: dict[str, RestaurantTemplate] = {}
    current_restaurant: RestaurantTemplate | None = None

    for raw_line in raw_text.splitlines():
        line = _normalize_menu_line(raw_line)
        if not line or _should_ignore_line(line):
            continue

        item_match = MENU_ITEM_RE.match(line)
        if item_match:
            if current_restaurant is None:
                continue
            code = normalize_code(item_match.group(1))
            name, description = _split_item_text(item_match.group(2).strip())
            item = MenuItem(
                code=code,
                restaurant=current_restaurant.name,
                name=name,
                description=description,
                free_text=any(keyword in name for keyword in FREE_TEXT_KEYWORDS),
            )
            _upsert_item(current_restaurant, item)
            continue

        restaurant_name, location = _parse_restaurant_line(line)
        if not restaurant_name:
            continue
        current_restaurant = restaurant_by_name.get(restaurant_name)
        if current_restaurant is None:
            current_restaurant = RestaurantTemplate(name=restaurant_name, location=location)
            restaurants.append(current_restaurant)
            restaurant_by_name[restaurant_name] = current_restaurant
        elif location:
            current_restaurant.location = location

    return MenuTemplateStore(restaurants=restaurants)


def _normalize_menu_line(line: str) -> str:
    return unicodedata.normalize("NFKC", line).strip()


def _should_ignore_line(line: str) -> bool:
    ignored_fragments = ("接龙", "疯狂星期四", "请大家", "👇")
    return ORDER_LINE_RE.match(line) is not None or any(
        fragment in line for fragment in ignored_fragments
    )


def _parse_restaurant_line(line: str) -> tuple[str, str]:
    special_match = re.match(r"^特别节目[（(](.+?)[）)]\s*$", line)
    if special_match:
        return special_match.group(1).strip(), ""

    match = PARENS_RE.match(line)
    if match:
        return match.group(1).strip(), match.group(2).strip()

    return line.strip(), ""


def _split_item_text(text: str) -> tuple[str, str]:
    match = PARENS_RE.match(text)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return text.strip(), ""


def _upsert_item(restaurant: RestaurantTemplate, item: MenuItem) -> None:
    for index, existing in enumerate(restaurant.items):
        if existing.code == item.code:
            restaurant.items[index] = item
            return
    restaurant.items.append(item)
