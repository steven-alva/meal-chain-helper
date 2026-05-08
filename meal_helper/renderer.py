import json
from dataclasses import asdict
from itertools import groupby

from meal_helper.aggregator import group_orders_by_restaurant_and_item
from meal_helper.models import ParseResult


def render_manager_summary(parse_result: ParseResult) -> str:
    lines = ["🍱 今日下单清单"]
    grouped = group_orders_by_restaurant_and_item(parse_result)

    for restaurant, summaries_iter in groupby(grouped, key=lambda summary: summary.restaurant):
        lines.extend(["", restaurant, ""])
        summaries = list(summaries_iter)
        for summary_index, summary in enumerate(summaries):
            if summary_index:
                lines.append("")
            lines.append(f"{summary.item_code} {summary.item_name} x{summary.count}")
            for order in summary.orders:
                note = order.note or "未填写备注"
                lines.append(f"- {order.name}：{note}")

    if parse_result.unresolved:
        lines.extend(["", "⚠️ 需要确认", ""])
        for index, unresolved in enumerate(parse_result.unresolved):
            if index:
                lines.append("")
            lines.append(unresolved.raw_line)
            lines.append(f"原因：{unresolved.reason}")
            if unresolved.suggestion:
                lines.append(f"建议：{unresolved.suggestion}")

    if parse_result.duplicates:
        lines.extend(["", "🔁 重复提交", ""])
        for duplicate in parse_result.duplicates:
            lines.append(
                f"{duplicate.name}：保留 {duplicate.kept.raw_line}；替换 {duplicate.discarded.raw_line}"
            )

    return "\n".join(lines).strip() + "\n"


def render_parse_debug_json(parse_result: ParseResult) -> str:
    return json.dumps(asdict(parse_result), ensure_ascii=False, indent=2)

