from collections import OrderedDict

from meal_helper.models import GroupedSummary, ParseResult, ParsedOrder


def group_orders_by_restaurant_and_item(parse_result: ParseResult) -> list[GroupedSummary]:
    grouped: OrderedDict[tuple[str, str, str], list[ParsedOrder]] = OrderedDict()

    for order in parse_result.orders:
        key = (order.restaurant, order.code, order.item_name)
        grouped.setdefault(key, []).append(order)

    return [
        GroupedSummary(
            restaurant=restaurant,
            item_code=item_code,
            item_name=item_name,
            count=len(orders),
            orders=orders,
        )
        for (restaurant, item_code, item_name), orders in grouped.items()
    ]

