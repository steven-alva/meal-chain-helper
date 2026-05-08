from dataclasses import asdict
from pathlib import Path

import yaml

from meal_helper.models import MenuItem, MenuTemplateStore, RestaurantTemplate
from meal_helper.normalizer import normalize_code


def load_menu_templates(path: str) -> MenuTemplateStore:
    template_path = Path(path)
    if not template_path.exists():
        return MenuTemplateStore()

    data = yaml.safe_load(template_path.read_text(encoding="utf-8")) or {}
    restaurants = []
    for restaurant_data in data.get("restaurants", []):
        items = [
            MenuItem(
                code=normalize_code(str(item_data.get("code", ""))),
                restaurant=str(item_data.get("restaurant", restaurant_data.get("name", ""))),
                name=str(item_data.get("name", "")),
                description=str(item_data.get("description", "")),
                free_text=bool(item_data.get("free_text", False)),
            )
            for item_data in restaurant_data.get("items", [])
        ]
        restaurants.append(
            RestaurantTemplate(
                name=str(restaurant_data.get("name", "")),
                location=str(restaurant_data.get("location", "")),
                items=items,
            )
        )
    return MenuTemplateStore(restaurants=restaurants)


def save_menu_templates(store: MenuTemplateStore, path: str) -> None:
    template_path = Path(path)
    template_path.parent.mkdir(parents=True, exist_ok=True)
    payload = asdict(store)
    template_path.write_text(
        yaml.safe_dump(payload, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def merge_menu_templates(
    old_store: MenuTemplateStore, new_store: MenuTemplateStore
) -> MenuTemplateStore:
    merged_restaurants = [_copy_restaurant(restaurant) for restaurant in old_store.restaurants]
    restaurant_by_name = {restaurant.name: restaurant for restaurant in merged_restaurants}

    for new_restaurant in new_store.restaurants:
        if new_restaurant.name not in restaurant_by_name:
            copied = _copy_restaurant(new_restaurant)
            merged_restaurants.append(copied)
            restaurant_by_name[copied.name] = copied
            continue

        target = restaurant_by_name[new_restaurant.name]
        if new_restaurant.location:
            target.location = new_restaurant.location
        item_index_by_code = {item.code: index for index, item in enumerate(target.items)}
        for new_item in new_restaurant.items:
            copied_item = _copy_item(new_item)
            if copied_item.code in item_index_by_code:
                target.items[item_index_by_code[copied_item.code]] = copied_item
            else:
                item_index_by_code[copied_item.code] = len(target.items)
                target.items.append(copied_item)

    return MenuTemplateStore(restaurants=merged_restaurants)


def _copy_restaurant(restaurant: RestaurantTemplate) -> RestaurantTemplate:
    return RestaurantTemplate(
        name=restaurant.name,
        location=restaurant.location,
        items=[_copy_item(item) for item in restaurant.items],
    )


def _copy_item(item: MenuItem) -> MenuItem:
    return MenuItem(
        code=item.code,
        restaurant=item.restaurant,
        name=item.name,
        description=item.description,
        free_text=item.free_text,
    )

