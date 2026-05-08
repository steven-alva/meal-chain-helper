from pathlib import Path
from html import escape
import random
import sys

import streamlit as st
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from meal_helper.history_parser import extract_menu_templates
from meal_helper.aggregator import group_orders_by_restaurant_and_item
from meal_helper.menu_generator import generate_group_message
from meal_helper.menu_store import (
    load_menu_templates,
    merge_menu_templates,
    save_menu_templates,
)
from meal_helper.models import MenuItem, MenuTemplateStore, TodayMenu
from meal_helper.normalizer import normalize_code
from meal_helper.order_parser import parse_orders
from meal_helper.renderer import render_manager_summary, render_parse_debug_json


DATA_DIR = PROJECT_ROOT / "data"
MENU_TEMPLATE_PATH = DATA_DIR / "menu_templates.yml"
TITLE_HISTORY_PATH = DATA_DIR / "title_history.yml"
SAMPLE_HISTORY_PATH = DATA_DIR / "sample_history.txt"
SAMPLE_TODAY_CHAIN_PATH = DATA_DIR / "sample_today_chain.txt"
DEFAULT_TITLE = "#接龙🥗轻食 5/8 接力棒棒棒🏃‍♀️🏃‍♂️"
MENU_STATE_VERSION = 2
DEFAULT_TODAY_CHAIN_TEXT = """1. We.SNM
2. 冰✡️saya🫧 麦辣鸡腿堡 + 麦辣鸡翅 + 桃气醒醒气泡美式
3. 不要向我手指的方向看 E 烤🐔
4. Jaxon I 鸡胸球
5. Sirius I 三文鱼
6. Pepsi 凤梨板烧四件套
7. 小白的黑色幽默 K 🍤芦笋🥚
8. Jasper K🦐
9. hans J🐮
10. Bruce_Chen I 鸡胸
11. Henry I 鸡胸
"""


def main() -> None:
    st.set_page_config(page_title="接龙点餐小助手", page_icon="🍱", layout="wide")
    _apply_style()
    _ensure_session_state()
    _sanitize_session_stores()

    items = _all_available_items()
    selected_items_preview = _selected_items_from_state(items)
    parse_result = st.session_state.parse_result
    unresolved_count = len(parse_result.unresolved) if parse_result else 0
    order_count = len(parse_result.orders) if parse_result else 0

    st.markdown(
        """
        <section class="app-hero">
          <div>
            <div class="hero-kicker">TODAY'S LUNCH DESK</div>
            <h1>🍱 接龙点餐小助手</h1>
            <p>选今天菜单、复制群文案、粘贴接龙，一屏完成。</p>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    _render_dashboard_metrics(
        restaurant_count=len(st.session_state.template_store.restaurants),
        item_count=len(items),
        selected_count=len(selected_items_preview),
        order_count=order_count,
        unresolved_count=unresolved_count,
    )

    st.markdown(
        """
        <div class="step-strip">
          <div><strong>1</strong><span>勾选今日菜单</span></div>
          <div><strong>2</strong><span>生成群文案</span></div>
          <div><strong>3</strong><span>粘贴接龙出清单</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    menu_col, work_col = st.columns([0.92, 1.08], gap="large")
    with menu_col:
        selected_items = _render_menu_panel(items)

    today_menu = _build_today_menu(selected_items)

    with work_col:
        _render_message_panel(today_menu)
        _render_parse_panel(today_menu)

    _render_results_panel()
    _render_menu_maintenance()


def _render_dashboard_metrics(
    restaurant_count: int,
    item_count: int,
    selected_count: int,
    order_count: int,
    unresolved_count: int,
) -> None:
    st.markdown(
        f"""
        <section class="metric-grid">
          <div class="metric-card"><span>菜单库</span><strong>{restaurant_count}</strong><small>家餐厅</small></div>
          <div class="metric-card"><span>菜品池</span><strong>{item_count}</strong><small>个菜品</small></div>
          <div class="metric-card"><span>今日已选</span><strong>{selected_count}</strong><small>个选项</small></div>
          <div class="metric-card"><span>整理结果</span><strong>{order_count}</strong><small>单 · {unresolved_count} 条待确认</small></div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _render_menu_panel(items: list[MenuItem]) -> list[MenuItem]:
    st.markdown(
        """
        <section class="panel-title">
          <div class="panel-icon">🥗</div>
          <div>
            <h2>今日菜单</h2>
            <p>先选餐厅，再看菜品。发群时编号自动从 A 往下排。</p>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    if not items:
        st.info("菜单库还空着。打开下方「菜单库维护」先导入历史菜单～")
        return []

    selected_items: list[MenuItem] = []
    grouped: dict[str, list[tuple[int, MenuItem]]] = {}
    for index, item in enumerate(items):
        grouped.setdefault(item.restaurant, []).append((index, item))
    _ensure_item_selection_state(items)
    _ensure_restaurant_pool_state(grouped)
    _sync_restaurant_pool(grouped, st.session_state.restaurant_pool)

    toolbar_cols = st.columns([1, 1, 1], gap="small")
    with toolbar_cols[0]:
        if st.button("随机选 3 家", type="primary", use_container_width=True):
            restaurant_names = list(grouped)
            chosen = random.sample(restaurant_names, min(3, len(restaurant_names)))
            _select_restaurants(grouped, chosen)
            st.session_state.random_pick_note = ""
            _clear_order_outputs()
            st.rerun()
    with toolbar_cols[1]:
        if st.button("全部选上", use_container_width=True):
            _select_restaurants(grouped, list(grouped))
            st.session_state.random_pick_note = ""
            _clear_order_outputs()
            st.rerun()
    with toolbar_cols[2]:
        if st.button("先清空", use_container_width=True):
            _select_restaurants(grouped, [])
            st.session_state.random_pick_note = ""
            _clear_order_outputs()
            st.rerun()

    if st.session_state.random_pick_note:
        st.caption(st.session_state.random_pick_note)

    code_preview_by_key = _today_code_preview(items)
    selected_counts = {
        restaurant: _selected_count(restaurant, indexed_items)
        for restaurant, indexed_items in grouped.items()
    }

    st.markdown(
        """
        <div class="restaurant-picker-title">
          <strong>餐厅池</strong><span>点一下选中，再点一下取消</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    restaurant_entries = list(grouped.items())
    st.pills(
        "餐厅池",
        options=[restaurant for restaurant, _ in restaurant_entries],
        selection_mode="multi",
        format_func=lambda restaurant: _restaurant_pill_label(
            restaurant, selected_counts[restaurant], len(grouped[restaurant])
        ),
        key="restaurant_pool",
        label_visibility="collapsed",
    )

    selected_restaurants = [
        (restaurant, indexed_items)
        for restaurant, indexed_items in restaurant_entries
        if _restaurant_selected_by_state(restaurant)
    ]

    if not selected_restaurants:
        st.info("先从上面的餐厅池选 1 家或点「随机选 3 家」。")
        with st.expander("临时加一道菜"):
            _render_temp_item_form()
        return []

    st.markdown(
        """
        <div class="selected-menu-title">
          <strong>已选餐厅菜单</strong><span>只展开今天会发的餐厅</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    for restaurant, indexed_items in selected_restaurants:
        selected_in_group = selected_counts[restaurant]
        with st.container(border=True):
            st.markdown(
                f"""
                <div class="menu-card-head">
                  <div><strong>{_h(restaurant)}</strong><span>{selected_in_group}/{len(indexed_items)} 个已选</span></div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            group_cols = st.columns([1, 1, 3], gap="small")
            with group_cols[0]:
                if st.button("本店全选", key=f"select_all_{restaurant}", use_container_width=True):
                    _set_group_items(indexed_items, True)
                    _clear_order_outputs()
                    st.rerun()
            with group_cols[1]:
                if st.button("本店清空", key=f"clear_{restaurant}", use_container_width=True):
                    _set_group_items(indexed_items, False)
                    _clear_order_outputs()
                    st.rerun()

            for index, item in indexed_items:
                item_key = _item_key(index, item)
                today_code = code_preview_by_key.get(item_key, "—")
                checked = st.checkbox(
                    _today_item_label(item, today_code),
                    key=item_key,
                    on_change=_clear_order_outputs,
                )
                if checked:
                    selected_items.append(item)

    with st.expander("临时加一道菜"):
        _render_temp_item_form()

    return selected_items


def _render_message_panel(today_menu: TodayMenu) -> None:
    st.markdown(
        """
        <section class="panel-title compact">
          <div class="panel-icon">📣</div>
          <div>
            <h2>群文案</h2>
            <p>生成后直接复制到微信群。</p>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    _render_title_history_picker()
    title = st.text_input("今日标题", key="today_title")
    today_menu.title = title

    if st.button("生成今日群文案", type="primary", use_container_width=True):
        if not today_menu.selected_items:
            st.warning("先选几个今天要发的菜品吧～")
        else:
            st.session_state.today_menu = today_menu
            st.session_state.generated_message = generate_group_message(today_menu)
            _remember_title(today_menu.title)
            st.success("群文案生成好啦～")

    st.text_area(
        "可复制群文案",
        value=st.session_state.generated_message,
        height=220,
        placeholder="点上面的按钮后，这里会出现可以发群里的文案。",
    )


def _render_parse_panel(today_menu: TodayMenu) -> None:
    st.markdown(
        """
        <section class="panel-title compact">
          <div class="panel-icon">🧾</div>
          <div>
            <h2>接龙整理</h2>
            <p>把接龙贴进来，我来分餐厅和菜品。</p>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    today_chain_text = st.text_area(
        "今日接龙",
        height=220,
        placeholder="例如：1. Alex J 鸡胸",
        key="today_chain_text",
    )

    if st.button("整理下单清单", type="primary", use_container_width=True):
        if not today_menu.selected_items:
            st.warning("需要先确认今天有哪些菜品，我才能解析接龙～")
            return
        result = parse_orders(today_chain_text, today_menu)
        st.session_state.parse_result = result
        st.session_state.manager_summary = render_manager_summary(result)
        st.session_state.debug_json = render_parse_debug_json(result)
        st.rerun()


def _render_results_panel() -> None:
    if st.session_state.manager_summary:
        result = st.session_state.parse_result
        if not result:
            return
        if result and result.unresolved:
            st.warning("这些行我有点拿不准，需要你看一眼～")
        else:
            st.success("看起来都整理好啦～")

        _render_visual_order_summary(result)

        with st.expander("复制用纯文本"):
            st.text_area(
                "主管查看版下单清单",
                value=st.session_state.manager_summary,
                height=260,
            )

        if result and result.unresolved:
            with st.expander("异常明细"):
                for unresolved in result.unresolved:
                    st.markdown(
                        f"<div class='alert-line'>{unresolved.raw_line}<br><small>原因：{unresolved.reason}</small></div>",
                        unsafe_allow_html=True,
                    )

        with st.expander("JSON 调试信息"):
            st.code(st.session_state.debug_json, language="json")


def _render_visual_order_summary(parse_result) -> None:
    summaries = group_orders_by_restaurant_and_item(parse_result)
    restaurant_blocks: dict[str, list] = {}
    for summary in summaries:
        restaurant_blocks.setdefault(summary.restaurant, []).append(summary)

    total_orders = max(len(parse_result.orders), 1)
    restaurant_html_parts = []
    for restaurant, restaurant_summaries in restaurant_blocks.items():
        restaurant_count = sum(summary.count for summary in restaurant_summaries)
        restaurant_share = round(restaurant_count / total_orders * 100)
        dish_rows = []
        for summary in restaurant_summaries:
            order_chips = []
            for order in summary.orders:
                note = order.note or "未填写备注"
                warning = "<em>备注</em>" if order.warnings else ""
                order_chips.append(
                    "<span class='order-chip'>"
                    f"<span class='person-name'>{_h(order.name)}</span>"
                    f"<span class='order-note'>{_h(note)}{warning}</span>"
                    "</span>"
                )
            dish_rows.append(
                "<div class='dish-row'>"
                "<div class='dish-main'>"
                f"<span class='dish-code'>{_h(summary.item_code)}</span>"
                f"<strong>{_h(summary.item_name)}</strong>"
                f"<span class='dish-count'>x{summary.count}</span>"
                "</div>"
                f"<div class='order-chip-list'>{''.join(order_chips)}</div>"
                "</div>"
            )

        restaurant_html_parts.append(
            f"<section class='restaurant-card' style='--share:{restaurant_share}%;'>"
            "<div class='restaurant-head'>"
            "<div>"
            f"<h4>{_h(restaurant)}</h4>"
            f"<small>{len(restaurant_summaries)} 个菜品</small>"
            "</div>"
            f"<span>{restaurant_count} 单</span>"
            "</div>"
            "<div class='restaurant-meter'><i></i></div>"
            f"<div class='dish-table'>{''.join(dish_rows)}</div>"
            "</section>"
        )

    unresolved_html = ""
    if parse_result.unresolved:
        rows = []
        for unresolved in parse_result.unresolved:
            rows.append(
                "<div class='confirm-row'>"
                f"<strong>{_h(unresolved.raw_line)}</strong>"
                f"<span>{_h(unresolved.reason)}</span>"
                "</div>"
            )
        unresolved_html = (
            "<section class='confirm-card'>"
            "<div class='restaurant-head'><h4>需要确认</h4>"
            f"<span>{len(parse_result.unresolved)} 条</span></div>"
            f"{''.join(rows)}"
            "</section>"
        )

    duplicate_html = ""
    if parse_result.duplicates:
        rows = []
        for duplicate in parse_result.duplicates:
            rows.append(
                "<div class='confirm-row duplicate'>"
                f"<strong>{_h(duplicate.name)}</strong>"
                f"<span>保留：{_h(duplicate.kept.raw_line)}<br>替换：{_h(duplicate.discarded.raw_line)}</span>"
                "</div>"
            )
        duplicate_html = (
            "<section class='confirm-card'>"
            "<div class='restaurant-head'><h4>重复提交</h4>"
            f"<span>{len(parse_result.duplicates)} 人</span></div>"
            f"{''.join(rows)}"
            "</section>"
        )

    st.markdown(
        f"""
        <section class="order-board">
          <div class="order-board-head">
            <div>
              <span>主管查看版</span>
              <h3>今日下单清单</h3>
              <p>按餐厅聚合，按菜品归类，备注单独标出。</p>
            </div>
            <div class="order-board-stats">
              <div><strong>{len(parse_result.orders)}</strong><small>有效订单</small></div>
              <div><strong>{len(restaurant_blocks)}</strong><small>餐厅</small></div>
              <div><strong>{len(summaries)}</strong><small>菜品</small></div>
            </div>
          </div>
          <div class="restaurant-grid">{''.join(restaurant_html_parts)}</div>
          {unresolved_html}
          {duplicate_html}
        </section>
        """,
        unsafe_allow_html=True,
    )


def _render_title_history_picker() -> None:
    history = st.session_state.title_history
    if not history:
        return

    with st.expander("历史标题推荐"):
        st.caption("点一下就会填到今日标题里。")
        for index, title in enumerate(history[:6]):
            if st.button(title, key=f"title_history_{index}", use_container_width=True):
                st.session_state.today_title = title
                st.rerun()


def _render_menu_maintenance() -> None:
    st.markdown("---")
    with st.expander("菜单库维护：导入历史菜单 / 保存模板"):
        left, right = st.columns([1.08, 0.92], gap="large")
        with left:
            history_text = st.text_area(
                "历史菜单文本",
                value=_read_text(SAMPLE_HISTORY_PATH),
                height=240,
                placeholder="这里放历史菜单，不是今日接龙清单。",
            )
            col_extract, col_save, col_restore = st.columns(3)
            with col_extract:
                if st.button("提取菜单", use_container_width=True):
                    extracted = _drop_empty_restaurants(extract_menu_templates(history_text))
                    if _looks_like_order_chain(history_text) and not _store_has_items(extracted):
                        st.session_state.extracted_store = MenuTemplateStore()
                        st.warning("这段看起来像今日接龙清单，请贴到「接龙整理」里～")
                    elif not _store_has_items(extracted):
                        st.session_state.extracted_store = MenuTemplateStore()
                        st.warning("没有提取到菜单项，需要类似「A：菜品名」这样的行。")
                    else:
                        st.session_state.extracted_store = extracted
                        st.session_state.template_store = merge_menu_templates(
                            st.session_state.template_store, extracted
                        )
                        st.success("菜单提取好啦～")
            with col_save:
                if st.button("保存模板", use_container_width=True):
                    save_menu_templates(st.session_state.template_store, str(MENU_TEMPLATE_PATH))
                    st.success("已经保存好啦～")
            with col_restore:
                if st.button("恢复模板", use_container_width=True):
                    st.session_state.template_store = load_menu_templates(str(MENU_TEMPLATE_PATH))
                    st.session_state.extracted_store = MenuTemplateStore()
                    st.session_state.temp_items = []
                    st.success("已恢复到已保存的模板～")
                    st.rerun()

        with right:
            if st.session_state.extracted_store.restaurants:
                st.markdown("#### 新提取到的菜单")
                _render_store_preview(st.session_state.extracted_store, expanded=True)
            else:
                st.markdown("#### 当前菜单库")
                _render_store_preview(st.session_state.template_store, expanded=False)


def _render_temp_item_form() -> None:
    with st.form("temp_item_form", clear_on_submit=True):
        col_code, col_restaurant = st.columns([1, 2])
        with col_code:
            code = st.text_input("code")
        with col_restaurant:
            restaurant = st.text_input("餐厅")
        name = st.text_input("菜品名")
        description = st.text_input("描述")
        free_text = st.checkbox("这是自由文本菜品")
        submitted = st.form_submit_button("加入今日菜单")

        if submitted:
            if not code.strip() or not restaurant.strip() or not name.strip():
                st.warning("code、餐厅、菜品名都需要填一下～")
            else:
                item = MenuItem(
                    code=normalize_code(code),
                    restaurant=restaurant.strip(),
                    name=name.strip(),
                    description=description.strip(),
                    free_text=free_text,
                )
                st.session_state.temp_items.append(item)
                st.success("临时菜单项加好啦～")
                st.rerun()


def _build_today_menu(selected_items: list[MenuItem]) -> TodayMenu:
    today_items = _renumber_selected_items(selected_items)
    free_text_codes = [item.code for item in today_items if item.free_text]
    free_text_default_code = free_text_codes[0] if free_text_codes else None
    if len(free_text_codes) > 1:
        free_text_default_code = st.selectbox(
            "自由文本默认归到哪个 code",
            options=free_text_codes,
            key="free_text_code",
        )

    return TodayMenu(
        title=st.session_state.today_title,
        selected_items=today_items,
        free_text_default_code=free_text_default_code,
    )


def _render_store_preview(store: MenuTemplateStore, expanded: bool = False) -> None:
    for restaurant in store.restaurants:
        label = restaurant.name
        if restaurant.location:
            label += f"（{restaurant.location}）"
        with st.expander(label, expanded=expanded):
            for item in restaurant.items:
                st.markdown(
                    f"<div class='menu-line'>{_item_label(item)}</div>",
                    unsafe_allow_html=True,
                )


def _item_label(item: MenuItem) -> str:
    description = f" · {item.description}" if item.description else ""
    free_text = " · 自由文本" if item.free_text else ""
    return f"{item.code}  {item.name}{description}{free_text}"


def _today_item_label(item: MenuItem, today_code: str) -> str:
    description = f" · {item.description}" if item.description else ""
    free_text = " · 自由文本" if item.free_text else ""
    return f"{today_code}  {item.name}{description}{free_text}"


def _h(value: object) -> str:
    return escape(str(value), quote=False)


def _item_key(index: int, item: MenuItem) -> str:
    return f"dashboard_item_{index}_{item.restaurant}_{item.code}"


def _item_selected_by_state(index: int, item: MenuItem) -> bool:
    return bool(st.session_state.get(_item_key(index, item), True))


def _restaurant_selected_by_state(restaurant: str) -> bool:
    return restaurant in st.session_state.get("restaurant_pool", [])


def _ensure_item_selection_state(items: list[MenuItem]) -> None:
    for index, item in enumerate(items):
        st.session_state.setdefault(_item_key(index, item), True)


def _ensure_restaurant_pool_state(grouped: dict[str, list[tuple[int, MenuItem]]]) -> None:
    valid_restaurants = set(grouped)
    current = [
        restaurant
        for restaurant in st.session_state.get("restaurant_pool", [])
        if restaurant in valid_restaurants
    ]
    previous = [
        restaurant
        for restaurant in st.session_state.get("restaurant_pool_previous", [])
        if restaurant in valid_restaurants
    ]
    st.session_state.restaurant_pool = current
    st.session_state.restaurant_pool_previous = previous


def _all_available_items() -> list[MenuItem]:
    return _flatten_store_items(st.session_state.template_store) + st.session_state.temp_items


def _selected_items_from_state(items: list[MenuItem]) -> list[MenuItem]:
    return [
        item
        for index, item in enumerate(items)
        if _restaurant_selected_by_state(item.restaurant)
        and _item_selected_by_state(index, item)
    ]


def _today_code_preview(items: list[MenuItem]) -> dict[str, str]:
    code_by_key: dict[str, str] = {}
    next_code_index = 0
    for index, item in enumerate(items):
        if not _restaurant_selected_by_state(item.restaurant):
            continue
        if not _item_selected_by_state(index, item):
            continue
        code_by_key[_item_key(index, item)] = _auto_code(next_code_index)
        next_code_index += 1
    return code_by_key


def _renumber_selected_items(items: list[MenuItem]) -> list[MenuItem]:
    return [
        MenuItem(
            code=_auto_code(index),
            restaurant=item.restaurant,
            name=item.name,
            description=item.description,
            free_text=item.free_text,
        )
        for index, item in enumerate(items)
    ]


def _auto_code(index: int) -> str:
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    code = ""
    value = index
    while True:
        value, remainder = divmod(value, len(letters))
        code = letters[remainder] + code
        if value == 0:
            return code
        value -= 1


def _set_group_items(indexed_items: list[tuple[int, MenuItem]], selected: bool) -> None:
    for index, item in indexed_items:
        st.session_state[_item_key(index, item)] = selected


def _selected_count(restaurant: str, indexed_items: list[tuple[int, MenuItem]]) -> int:
    if not _restaurant_selected_by_state(restaurant):
        return 0
    return sum(1 for index, item in indexed_items if _item_selected_by_state(index, item))


def _select_restaurants(
    grouped: dict[str, list[tuple[int, MenuItem]]], selected_restaurants: list[str]
) -> None:
    valid_selection = [restaurant for restaurant in selected_restaurants if restaurant in grouped]
    selected_set = set(valid_selection)
    for restaurant, indexed_items in grouped.items():
        if restaurant in selected_set:
            _set_group_items(indexed_items, True)
    st.session_state.restaurant_pool = valid_selection
    st.session_state.restaurant_pool_previous = valid_selection


def _sync_restaurant_pool(
    grouped: dict[str, list[tuple[int, MenuItem]]], selected_restaurants: list[str] | None
) -> None:
    selected = [restaurant for restaurant in (selected_restaurants or []) if restaurant in grouped]
    previous = [
        restaurant
        for restaurant in st.session_state.get("restaurant_pool_previous", [])
        if restaurant in grouped
    ]
    newly_selected = set(selected) - set(previous)
    for restaurant in newly_selected:
        _set_group_items(grouped[restaurant], True)
    if set(selected) != set(previous):
        st.session_state.random_pick_note = ""
        _clear_order_outputs()
    st.session_state.restaurant_pool = selected
    st.session_state.restaurant_pool_previous = selected


def _restaurant_pill_label(restaurant: str, selected_count: int, total_count: int) -> str:
    return f"{restaurant} {selected_count}/{total_count}"


def _clear_order_outputs() -> None:
    st.session_state.generated_message = ""
    st.session_state.parse_result = None
    st.session_state.manager_summary = ""
    st.session_state.debug_json = ""


def _flatten_store_items(store: MenuTemplateStore) -> list[MenuItem]:
    return [item for restaurant in store.restaurants for item in restaurant.items]


def _store_has_items(store: MenuTemplateStore) -> bool:
    return any(restaurant.items for restaurant in store.restaurants)


def _looks_like_order_chain(raw_text: str) -> bool:
    order_like_lines = 0
    non_empty_lines = 0
    for raw_line in raw_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        non_empty_lines += 1
        if line[0].isdigit() and any(
            separator in line[:4] for separator in (".", "、", ")", "）")
        ):
            order_like_lines += 1
    return non_empty_lines > 0 and order_like_lines / non_empty_lines >= 0.5


def _ensure_session_state() -> None:
    defaults = {
        "template_store": load_menu_templates(str(MENU_TEMPLATE_PATH)),
        "extracted_store": MenuTemplateStore(),
        "temp_items": [],
        "today_menu": TodayMenu(title=DEFAULT_TITLE),
        "today_title": DEFAULT_TITLE,
        "title_history": _load_title_history(),
        "today_chain_text": DEFAULT_TODAY_CHAIN_TEXT,
        "generated_message": "",
        "parse_result": None,
        "manager_summary": "",
        "debug_json": "",
        "random_pick_note": "",
        "restaurant_pool": [],
        "restaurant_pool_previous": [],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    if st.session_state.get("menu_state_version") != MENU_STATE_VERSION:
        st.session_state.restaurant_pool = []
        st.session_state.restaurant_pool_previous = []
        st.session_state.random_pick_note = ""
        _clear_order_outputs()
        st.session_state.menu_state_version = MENU_STATE_VERSION


def _sanitize_session_stores() -> None:
    st.session_state.template_store = _drop_empty_restaurants(st.session_state.template_store)
    st.session_state.extracted_store = _drop_empty_restaurants(st.session_state.extracted_store)


def _drop_empty_restaurants(store: MenuTemplateStore) -> MenuTemplateStore:
    return MenuTemplateStore(
        restaurants=[restaurant for restaurant in store.restaurants if restaurant.items]
    )


def _read_text(path: Path) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def _load_title_history() -> list[str]:
    default_titles = [
        DEFAULT_TITLE,
        "#接龙🥗午饭 5/8 今天吃点好的～",
        "#接龙🍱晚饭 5/8 接一下～",
    ]
    if not TITLE_HISTORY_PATH.exists():
        return default_titles

    data = yaml.safe_load(TITLE_HISTORY_PATH.read_text(encoding="utf-8")) or {}
    loaded_titles = data.get("titles", [])
    titles = [title for title in loaded_titles if isinstance(title, str) and title.strip()]
    for title in default_titles:
        if title not in titles:
            titles.append(title)
    return titles[:8]


def _remember_title(title: str) -> None:
    clean_title = title.strip()
    if not clean_title:
        return

    history = [existing for existing in st.session_state.title_history if existing != clean_title]
    history.insert(0, clean_title)
    st.session_state.title_history = history[:8]
    TITLE_HISTORY_PATH.write_text(
        yaml.safe_dump(
            {"titles": st.session_state.title_history},
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def _apply_style() -> None:
    st.markdown(
        """
        <style>
        :root {
            --ink: #30251f;
            --muted: #786357;
            --line: #ead8c8;
            --paper: #fffaf2;
            --card: #ffffff;
            --accent: #d7643a;
            --mint: #dff2df;
            --lemon: #fff0b8;
            --rose: #ffe7e0;
            --peach: #ffeadc;
        }
        [data-testid="stHeader"],
        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        .stDeployButton {
            display: none !important;
        }
        .stApp {
            background:
                linear-gradient(90deg, rgba(232, 216, 200, 0.22) 1px, transparent 1px),
                linear-gradient(180deg, rgba(232, 216, 200, 0.18) 1px, transparent 1px),
                var(--paper);
            background-size: 32px 32px;
            color: var(--ink);
        }
        .block-container {
            max-width: 1220px;
            padding-top: 16px;
            padding-bottom: 52px;
        }
        h1, h2, h3, h4, h5, h6, p, label, span, div {
            color: var(--ink);
            letter-spacing: 0;
        }
        .app-hero {
            display: flex;
            align-items: center;
            justify-content: flex-start;
            gap: 20px;
            border: 1px solid var(--line);
            background: #fffdf9;
            border-radius: 8px;
            padding: 16px 18px;
            margin-bottom: 12px;
            box-shadow: 0 10px 24px rgba(92, 62, 40, 0.06);
        }
        .app-hero .hero-kicker {
            color: var(--accent);
            font-size: 12px;
            font-weight: 900;
            margin-bottom: 6px;
            text-transform: uppercase;
        }
        .app-hero h1 {
            font-size: 32px;
            line-height: 1.12;
            margin: 0 0 6px;
        }
        .app-hero p {
            color: var(--muted);
            font-size: 15px;
            margin: 0;
        }
        .metric-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 8px;
            margin: 0 0 10px;
        }
        .metric-card {
            border: 1px solid var(--line);
            border-left: 4px solid #df815e;
            background: rgba(255, 255, 255, 0.9);
            border-radius: 8px;
            padding: 10px 12px;
            box-shadow: 0 8px 18px rgba(92, 62, 40, 0.05);
        }
        .metric-card span {
            display: block;
            color: var(--muted);
            font-size: 13px;
            font-weight: 800;
        }
        .metric-card strong {
            display: block;
            color: var(--ink);
            font-size: 25px;
            line-height: 1;
            margin: 6px 0 4px;
        }
        .metric-card small {
            color: var(--muted);
            font-size: 13px;
        }
        .step-strip {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 8px;
            margin: 0 0 12px;
        }
        .step-strip > div {
            display: flex;
            align-items: center;
            gap: 10px;
            border: 1px solid var(--line);
            background: rgba(255, 255, 255, 0.78);
            border-radius: 8px;
            padding: 8px 10px;
        }
        .step-strip strong {
            display: inline-grid;
            place-items: center;
            width: 26px;
            height: 26px;
            border-radius: 50%;
            background: var(--accent);
            color: #fff;
            font-size: 14px;
        }
        .step-strip span {
            color: var(--muted);
            font-weight: 800;
        }
        .panel-title {
            display: flex;
            align-items: center;
            gap: 12px;
            margin: 8px 0 12px;
        }
        .panel-title.compact {
            margin-top: 4px;
        }
        .panel-title .panel-icon {
            display: inline-grid;
            place-items: center;
            width: 42px;
            height: 42px;
            border-radius: 8px;
            background: #fff;
            border: 1px solid var(--line);
            font-size: 23px;
        }
        .panel-title h2 {
            margin: 0;
            font-size: 25px;
            line-height: 1.2;
        }
        .panel-title p {
            margin: 3px 0 0;
            color: var(--muted);
            font-size: 14px;
        }
        .menu-line {
            padding: 7px 0;
            border-bottom: 1px dashed #eadfd5;
            line-height: 1.55;
        }
        .restaurant-picker-title,
        .selected-menu-title {
            display: flex;
            align-items: baseline;
            justify-content: space-between;
            gap: 10px;
            margin: 12px 0 7px;
        }
        .restaurant-picker-title strong,
        .selected-menu-title strong {
            font-size: 15px;
            line-height: 1.25;
        }
        .restaurant-picker-title span,
        .selected-menu-title span {
            color: var(--muted);
            font-size: 12px;
            font-weight: 800;
            text-align: right;
        }
        div[data-testid="stPills"] button {
            min-height: 30px;
            padding: 3px 9px;
            border-radius: 999px;
            font-size: 13px;
            font-weight: 800;
        }
        .menu-card-head {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            padding: 1px 0 8px;
            border-bottom: 1px solid #f0e5db;
            margin-bottom: 8px;
        }
        .menu-card-head strong {
            display: block;
            font-size: 16px;
            line-height: 1.25;
        }
        .menu-card-head span {
            display: block;
            color: var(--accent);
            font-size: 12px;
            font-weight: 900;
            margin-top: 2px;
        }
        div[data-testid="stCheckbox"] {
            border-bottom: 1px dashed #f0e5db;
            padding: 3px 0 5px;
        }
        div[data-testid="stCheckbox"]:last-child {
            border-bottom: 0;
        }
        div[data-testid="stCheckbox"] label {
            align-items: flex-start;
        }
        div[data-testid="stCheckbox"] p {
            line-height: 1.45;
        }
        .order-board {
            border: 1px solid var(--line);
            background: rgba(255, 255, 255, 0.9);
            border-radius: 8px;
            padding: 14px;
            margin: 18px 0 14px;
            box-shadow: 0 10px 24px rgba(92, 62, 40, 0.06);
        }
        .order-board-head {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            border-bottom: 1px solid #efe0d4;
            padding-bottom: 10px;
            margin-bottom: 10px;
        }
        .order-board-head span {
            display: block;
            color: var(--accent);
            font-size: 12px;
            font-weight: 900;
            margin-bottom: 3px;
        }
        .order-board-head h3 {
            font-size: 23px;
            line-height: 1.2;
            margin: 0;
        }
        .order-board-head p {
            margin: 4px 0 0;
            color: var(--muted);
            font-size: 13px;
        }
        .order-board-stats {
            display: grid;
            grid-template-columns: repeat(3, minmax(74px, 1fr));
            gap: 7px;
            min-width: 270px;
        }
        .order-board-stats div {
            border: 1px solid var(--line);
            background: #fff9ef;
            border-radius: 8px;
            padding: 8px 9px;
            text-align: center;
        }
        .order-board-stats strong {
            display: block;
            font-size: 23px;
            line-height: 1;
        }
        .order-board-stats small {
            color: var(--muted);
            font-size: 11px;
            font-weight: 800;
        }
        .restaurant-grid {
            columns: 2 420px;
            column-gap: 10px;
        }
        .restaurant-card,
        .confirm-card {
            border: 1px solid #eadfd5;
            background: #fffdf9;
            border-radius: 8px;
            padding: 9px 10px 10px;
            overflow: hidden;
        }
        .restaurant-card {
            display: inline-block;
            width: 100%;
            break-inside: avoid;
            margin: 0 0 10px;
        }
        .confirm-card {
            margin-top: 10px;
        }
        .restaurant-head {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            padding-bottom: 6px;
            margin-bottom: 0;
        }
        .restaurant-head h4 {
            font-size: 16px;
            line-height: 1.25;
            margin: 0;
        }
        .restaurant-head small {
            display: block;
            color: var(--muted);
            font-size: 11px;
            font-weight: 800;
            margin-top: 2px;
        }
        .restaurant-head span {
            flex: 0 0 auto;
            border: 1px solid #f0d2bf;
            background: #fff2e9;
            border-radius: 999px;
            color: var(--accent);
            font-size: 12px;
            font-weight: 900;
            padding: 4px 9px;
        }
        .restaurant-meter {
            height: 5px;
            overflow: hidden;
            border-radius: 999px;
            background: #f4e8de;
            margin: 0 0 4px;
        }
        .restaurant-meter i {
            display: block;
            height: 100%;
            width: var(--share);
            min-width: 8%;
            border-radius: inherit;
            background: var(--accent);
        }
        .dish-table {
            display: grid;
        }
        .dish-row {
            display: grid;
            grid-template-columns: minmax(128px, 0.32fr) 1fr;
            gap: 8px;
            border-bottom: 1px solid #f0e5db;
            padding: 8px 0;
        }
        .dish-row:last-child {
            border-bottom: 0;
            padding-bottom: 0;
        }
        .dish-main {
            display: grid;
            grid-template-columns: 24px 1fr auto;
            align-content: start;
            gap: 4px 7px;
            min-width: 0;
        }
        .dish-code {
            display: inline-grid;
            place-items: center;
            min-width: 24px;
            height: 24px;
            border-radius: 8px;
            background: #f6e4d7;
            color: var(--accent);
            font-weight: 950;
            font-size: 12px;
        }
        .dish-main strong {
            font-size: 14px;
            line-height: 1.25;
            overflow-wrap: anywhere;
        }
        .dish-count {
            justify-self: end;
            align-self: start;
            background: var(--accent);
            color: #fff;
            border-radius: 999px;
            padding: 3px 7px;
            font-size: 11px;
            font-weight: 900;
        }
        .order-chip-list {
            display: flex;
            flex-wrap: wrap;
            gap: 5px;
            align-content: start;
            min-width: 0;
        }
        .order-chip {
            display: inline-flex;
            align-items: baseline;
            gap: 4px;
            max-width: 100%;
            border: 1px solid #efe0d4;
            background: #fff;
            border-radius: 7px;
            padding: 3px 6px;
            line-height: 1.25;
            font-size: 13px;
        }
        .person-name {
            color: var(--ink);
            font-weight: 900;
            overflow-wrap: anywhere;
            white-space: nowrap;
        }
        .order-note {
            color: var(--muted);
            overflow-wrap: anywhere;
            min-width: 0;
        }
        .order-note em {
            display: inline-block;
            margin-left: 4px;
            border-radius: 999px;
            background: #fff3cd;
            color: #8a621a;
            font-size: 10px;
            font-style: normal;
            font-weight: 900;
            padding: 1px 5px;
        }
        .alert-line {
            background: #fff6dd;
            border: 1px solid #f0d79c;
            border-radius: 8px;
            padding: 10px 12px;
            margin-bottom: 8px;
            line-height: 1.6;
        }
        .alert-line small {
            color: var(--muted);
        }
        .confirm-row {
            border-top: 1px dashed #eadfd5;
            padding: 8px 0 2px;
            line-height: 1.5;
        }
        .confirm-row strong,
        .confirm-row span {
            display: block;
        }
        .confirm-row span {
            color: var(--muted);
            margin-top: 3px;
        }
        div.stButton > button {
            border-radius: 8px;
            border-color: var(--line);
            color: var(--ink);
            font-weight: 800;
        }
        div.stButton > button[kind="primary"] {
            background: var(--accent);
            border-color: var(--accent);
            color: #fff;
        }
        div.stButton > button[kind="primary"] *,
        button[data-testid="stBaseButton-primary"] * {
            color: #fff !important;
        }
        div[data-testid="stExpander"] {
            border-color: var(--line);
            background: rgba(255, 255, 255, 0.82);
            border-radius: 8px;
        }
        div[data-testid="stTextArea"] textarea,
        div[data-testid="stTextInput"] input {
            background: #fff !important;
            color: var(--ink) !important;
            border: 1px solid var(--line) !important;
            border-radius: 8px !important;
            font-size: 15px !important;
            line-height: 1.55 !important;
        }
        [data-testid="stWidgetLabel"] p,
        [data-testid="stMarkdownContainer"] p {
            color: var(--ink);
        }
        @media (max-width: 860px) {
            .app-hero {
                padding: 18px 16px;
            }
            .app-hero h1 {
                font-size: 30px;
            }
        }
        @media (max-width: 520px) {
            .metric-grid {
                grid-template-columns: 1fr 1fr;
            }
            .step-strip {
                grid-template-columns: 1fr;
            }
            .restaurant-grid {
                grid-template-columns: 1fr;
            }
            .dish-row {
                grid-template-columns: 1fr;
            }
            .person-name {
                white-space: normal;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
