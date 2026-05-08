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


def test_screenshot_style_menu_extracts_items():
    from meal_helper.history_parser import extract_menu_templates

    raw_text = """FLAG BENTO （星扬西岸店）
A:特色便当🍚（🐔🐷双拼/🐔🥑金枪鱼/豆腐/鸡胸/烤🐷/🦐/🥑）
B:意面🍝（奶油培根黑松露）
C:烩饭（翡翠鸡胸/翡翠🐔🐷/翡翠猪）
D:醋饭（芥末章鱼/中华小章鱼）

FitBee健康碗 （徐汇店）
E： 健康碗🍚/菠菜面（烤🐔/🍗/🦐/鸡胸/石锅🐮肉片）
"""

    store = extract_menu_templates(raw_text)
    restaurants = {restaurant.name: restaurant for restaurant in store.restaurants}

    assert list(restaurants) == ["FLAG BENTO", "FitBee健康碗"]
    assert restaurants["FLAG BENTO"].location == "星扬西岸店"
    assert [item.code for item in restaurants["FLAG BENTO"].items] == ["A", "B", "C", "D"]
    assert restaurants["FLAG BENTO"].items[0].name == "特色便当🍚"
    assert restaurants["FitBee健康碗"].location == "徐汇店"
    assert [item.code for item in restaurants["FitBee健康碗"].items] == ["E"]
    assert restaurants["FitBee健康碗"].items[0].name == "健康碗🍚/菠菜面"


def test_reused_item_codes_do_not_empty_previous_restaurants():
    from meal_helper.history_parser import extract_menu_templates

    raw_text = """第一家
A: 招牌饭

第二家
A: 健康碗
"""

    store = extract_menu_templates(raw_text)
    restaurants = {restaurant.name: restaurant for restaurant in store.restaurants}

    assert [item.name for item in restaurants["第一家"].items] == ["招牌饭"]
    assert [item.name for item in restaurants["第二家"].items] == ["健康碗"]


def test_full_width_codes_and_loose_separators_extract():
    from meal_helper.history_parser import extract_menu_templates

    raw_text = """测试餐厅（门店）
Ａ：全角冒号菜（描述）
B. 点号菜
C、顿号菜
D）括号菜
"""

    store = extract_menu_templates(raw_text)
    restaurant = store.restaurants[0]

    assert restaurant.name == "测试餐厅"
    assert restaurant.location == "门店"
    assert [item.code for item in restaurant.items] == ["A", "B", "C", "D"]
    assert [item.name for item in restaurant.items] == ["全角冒号菜", "点号菜", "顿号菜", "括号菜"]
    assert restaurant.items[0].description == "描述"
