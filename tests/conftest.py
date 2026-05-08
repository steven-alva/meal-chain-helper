from pathlib import Path

import pytest

from meal_helper.history_parser import extract_menu_templates
from meal_helper.models import TodayMenu


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def sample_history_text() -> str:
    return (PROJECT_ROOT / "data" / "sample_history.txt").read_text(encoding="utf-8")


@pytest.fixture
def sample_today_chain_text() -> str:
    return (PROJECT_ROOT / "data" / "sample_today_chain.txt").read_text(encoding="utf-8")


@pytest.fixture
def sample_store(sample_history_text):
    return extract_menu_templates(sample_history_text)


@pytest.fixture
def sample_today_menu(sample_store):
    selected_items = [
        item for restaurant in sample_store.restaurants for item in restaurant.items
    ]
    return TodayMenu(
        title="#接龙🥗轻食 5/8 接力棒棒棒🏃‍♀️🏃‍♂️",
        selected_items=selected_items,
        free_text_default_code="I",
    )

