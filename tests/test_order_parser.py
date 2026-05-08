from meal_helper.order_parser import parse_orders


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

