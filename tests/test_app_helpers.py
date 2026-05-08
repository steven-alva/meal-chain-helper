from datetime import date

from app.streamlit_app import _date_label, _default_title


def test_default_title_uses_supplied_date():
    assert _date_label(date(2026, 5, 9)) == "5/9"
    assert _default_title(date(2026, 5, 9)) == "#接龙🥗轻食 5/9 接力棒棒棒🏃‍♀️🏃‍♂️"
