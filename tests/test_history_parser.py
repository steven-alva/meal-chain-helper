def test_sample_history_extracts_restaurants_and_items(sample_store):
    restaurants = {restaurant.name: restaurant for restaurant in sample_store.restaurants}

    assert list(restaurants) == ["FLAG BENTO", "FitBee健康碗", "FIKAWKA", "麦当劳"]
    assert [item.code for item in restaurants["FLAG BENTO"].items] == ["A", "B", "C", "D"]
    assert [item.code for item in restaurants["FitBee健康碗"].items] == ["E", "F", "G", "H"]
    assert [item.code for item in restaurants["FIKAWKA"].items] == ["J", "K", "L", "M"]
    assert [item.code for item in restaurants["麦当劳"].items] == ["I"]

    assert restaurants["FLAG BENTO"].location == "星扬西岸店"
    assert restaurants["FitBee健康碗"].location == "徐汇店"

    mcdonalds_item = restaurants["麦当劳"].items[0]
    assert mcdonalds_item.free_text is True
    assert mcdonalds_item.name == "自选 50 元内项目"


def test_order_chain_lines_are_not_extracted_as_restaurants(sample_today_chain_text):
    from meal_helper.history_parser import extract_menu_templates

    store = extract_menu_templates(sample_today_chain_text)

    assert store.restaurants == []
