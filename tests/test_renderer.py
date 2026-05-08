from meal_helper.order_parser import parse_orders
from meal_helper.renderer import render_manager_summary


def test_render_manager_summary(sample_today_chain_text, sample_today_menu):
    result = parse_orders(sample_today_chain_text, sample_today_menu)
    summary = render_manager_summary(result)

    assert "🍱 今日下单清单" in summary
    assert "FIKAWKA" in summary
    assert "J 色拉🥗 x4" in summary
    assert "K 能量碗🍚 x1" in summary
    assert "L 意面🍝 x2" in summary
    assert "麦当劳" in summary
    assert "I 自选 50 元内项目 x2" in summary
    assert "⚠️ 需要确认" in summary
    assert "We.SNM" in summary

