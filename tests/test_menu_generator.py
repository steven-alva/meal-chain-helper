from meal_helper.menu_generator import generate_group_message
from meal_helper.models import TodayMenu


def test_generate_group_message_contains_selected_items(sample_store):
    restaurants = {restaurant.name: restaurant for restaurant in sample_store.restaurants}
    selected_items = [
        restaurants["FLAG BENTO"].items[0],
        restaurants["FLAG BENTO"].items[1],
        restaurants["FitBee健康碗"].items[0],
        restaurants["麦当劳"].items[0],
    ]
    message = generate_group_message(
        TodayMenu(title="#接龙🥗轻食 5/8 接力棒棒棒🏃‍♀️🏃‍♂️", selected_items=selected_items)
    )

    assert "FLAG BENTO" in message
    assert "A：" in message
    assert "特色便当🍚" in message
    assert "🐔🐷双拼" in message
    assert "请大家接龙" in message
    assert "特别节目（麦当劳）" in message

