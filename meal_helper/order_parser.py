import re

from meal_helper.models import (
    DuplicateOrder,
    MenuItem,
    ParsedOrder,
    ParseResult,
    TodayMenu,
    UnresolvedLine,
)
from meal_helper.normalizer import normalize_code, normalize_name


ORDER_LINE_RE = re.compile(r"^\s*(\d+)[\.\、\)\）]\s*(.+?)\s*$")
CODE_BOUNDARY_CHARS = r"A-Za-z0-9_"
UNRESOLVED_REASON = "未检测到菜品代码，也无法作为自由文本解析"


def parse_orders(raw_text: str, today_menu: TodayMenu) -> ParseResult:
    item_by_code = {
        normalize_code(item.code): item for item in today_menu.selected_items if item.code.strip()
    }
    code_re = _build_code_regex(item_by_code)
    free_text_item = _get_free_text_item(today_menu, item_by_code)

    unresolved: list[UnresolvedLine] = []
    duplicates: list[DuplicateOrder] = []
    kept_by_name: dict[str, ParsedOrder] = {}
    order_names: list[str] = []

    for raw_line in raw_text.splitlines():
        line = raw_line.strip()
        match = ORDER_LINE_RE.match(line)
        if not match:
            continue

        seq = int(match.group(1))
        body = match.group(2).strip()
        order = _parse_order_body(seq, body, line, item_by_code, code_re, free_text_item)
        if order is None:
            unresolved.append(
                UnresolvedLine(
                    seq=seq,
                    raw_line=line,
                    reason=UNRESOLVED_REASON,
                    suggestion="请手动确认是否点餐",
                )
            )
            continue

        name_key = normalize_name(order.name)
        if not name_key:
            unresolved.append(
                UnresolvedLine(
                    seq=seq,
                    raw_line=line,
                    reason="缺少点餐人姓名",
                    suggestion="请手动补充姓名",
                )
            )
            continue

        if name_key in kept_by_name:
            discarded = kept_by_name[name_key]
            duplicates.append(DuplicateOrder(name=order.name, kept=order, discarded=discarded))
            order_names.remove(name_key)
        kept_by_name[name_key] = order
        order_names.append(name_key)

    return ParseResult(
        orders=[kept_by_name[name_key] for name_key in order_names],
        unresolved=unresolved,
        duplicates=duplicates,
    )


def _parse_order_body(
    seq: int,
    body: str,
    raw_line: str,
    item_by_code: dict[str, MenuItem],
    code_re: re.Pattern[str] | None,
    free_text_item: MenuItem | None,
) -> ParsedOrder | None:
    if code_re is not None:
        code_match = code_re.search(body)
        if code_match:
            code = normalize_code(code_match.group(1))
            item = item_by_code[code]
            name = body[: code_match.start()].strip()
            note = body[code_match.end() :].strip()
            warnings = []
            confidence = 0.98
            if not note:
                warnings.append("未填写备注")
                confidence = 0.9
            return ParsedOrder(
                seq=seq,
                name=name,
                code=code,
                restaurant=item.restaurant,
                item_name=item.name,
                note=note,
                raw_line=raw_line,
                confidence=confidence,
                warnings=warnings,
            )

    if free_text_item is not None and re.search(r"\s", body):
        name, note = body.split(maxsplit=1)
        if name.strip() and note.strip():
            return ParsedOrder(
                seq=seq,
                name=name.strip(),
                code=normalize_code(free_text_item.code),
                restaurant=free_text_item.restaurant,
                item_name=free_text_item.name,
                note=note.strip(),
                raw_line=raw_line,
                confidence=0.75,
                warnings=["自由文本解析，请确认"],
            )

    return None


def _build_code_regex(item_by_code: dict[str, MenuItem]) -> re.Pattern[str] | None:
    codes = [re.escape(code) for code in sorted(item_by_code, key=len, reverse=True)]
    if not codes:
        return None
    alternatives = "|".join(codes)
    return re.compile(
        rf"(?<![{CODE_BOUNDARY_CHARS}])({alternatives})(?![{CODE_BOUNDARY_CHARS}])",
        re.IGNORECASE,
    )


def _get_free_text_item(
    today_menu: TodayMenu, item_by_code: dict[str, MenuItem]
) -> MenuItem | None:
    if not today_menu.free_text_default_code:
        return None
    item = item_by_code.get(normalize_code(today_menu.free_text_default_code))
    if item and item.free_text:
        return item
    return None

