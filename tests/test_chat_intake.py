from meal_helper.chat_intake import build_menu_context_from_chat
from meal_helper.order_parser import parse_orders


def test_full_chat_menu_is_used_for_order_grouping():
    raw_text = """#接龙🥗轻食 5/8 接力棒棒棒🏃‍♀️🏃‍♂️

牛气餐厅
C：牛肋条
D：鸡腿
E：牛
F：香肠
H：三鲜
J：喜三鲜

请大家接龙：
6. Lqz13Th E 🐮
7. 冰✡️saya 🫧 C 牛肋条
8. Bruce_Chen C🐔🐮
9. Jaxon 喜三鲜
10. Henry D 烤牛 不要酱+青椒洋葱+酸黄瓜酸辣椒
11. W E 牛
12. Furyfrog H 三鲜
13. hans h三鲜
"""

    context = build_menu_context_from_chat(raw_text)
    result = parse_orders(raw_text, context.menu)
    orders_by_seq = {order.seq: order for order in result.orders}

    assert context.source == "chat"
    assert "1 家餐厅、6 个菜品" in context.note
    assert len(result.orders) == 8
    assert result.unresolved == []
    assert {order.restaurant for order in result.orders} == {"牛气餐厅"}

    assert orders_by_seq[6].code == "E"
    assert orders_by_seq[6].item_name == "牛"
    assert orders_by_seq[7].code == "C"
    assert orders_by_seq[9].code == "J"
    assert orders_by_seq[9].item_name == "喜三鲜"
    assert orders_by_seq[13].code == "H"
