from meal_helper.order_parser import parse_orders
from meal_helper.models import TodayMenu


def test_sample_today_chain_parses_orders(sample_today_chain_text, sample_today_menu):
    result = parse_orders(sample_today_chain_text, sample_today_menu)
    orders_by_seq = {order.seq: order for order in result.orders}

    assert len(result.orders) == 10
    assert len(result.unresolved) == 1
    assert result.unresolved[0].raw_line == "1. We.SNM"

    assert orders_by_seq[2].code == "I"
    assert orders_by_seq[2].restaurant == "麦当劳"
    assert orders_by_seq[2].item_name == "自选 50 元内项目"
    assert orders_by_seq[6].code == "I"
    assert orders_by_seq[6].restaurant == "麦当劳"
    assert orders_by_seq[6].item_name == "自选 50 元内项目"

    assert orders_by_seq[3].code == "E"
    assert [orders_by_seq[seq].code for seq in (4, 5, 10, 11)] == ["J", "J", "J", "J"]
    assert [orders_by_seq[seq].code for seq in (7, 8)] == ["L", "L"]
    assert orders_by_seq[9].code == "K"

    assert orders_by_seq[4].name == "Jaxon"
    assert orders_by_seq[10].name == "Bruce_Chen"
    assert "自由文本解析，请确认" in orders_by_seq[2].warnings
    assert "自由文本解析，请确认" in orders_by_seq[6].warnings


def test_chain_can_be_visualized_without_today_menu():
    raw_text = """6. Lqz13Th E 🐮
7. 冰✡️saya 🫧 C 牛肋条
8. Bruce_Chen C🐔🐮
9. Jaxon 喜三鲜
10. Henry D 烤牛 不要酱+青椒洋葱+酸黄瓜酸辣椒
11. W E 牛
12. Furyfrog H 三鲜
13. hans h三鲜
"""

    result = parse_orders(raw_text, TodayMenu(title=""))
    orders_by_seq = {order.seq: order for order in result.orders}

    assert len(result.orders) == 8
    assert result.unresolved == []

    assert orders_by_seq[6].restaurant == "待匹配菜单"
    assert orders_by_seq[6].code == "E"
    assert orders_by_seq[6].item_name == "选项 E"
    assert orders_by_seq[6].note == "🐮"

    assert orders_by_seq[7].name == "冰✡️saya 🫧"
    assert orders_by_seq[7].code == "C"
    assert orders_by_seq[8].code == "C"
    assert orders_by_seq[9].code == "手填"
    assert orders_by_seq[9].item_name == "喜三鲜"
    assert orders_by_seq[13].code == "H"
    assert orders_by_seq[13].note == "三鲜"
    assert "未绑定今日菜单，请确认菜品" in orders_by_seq[6].warnings
