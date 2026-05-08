def normalize_code(code: str) -> str:
    return code.strip().upper()


def normalize_name(name: str) -> str:
    return "".join(name.strip().lower().split())

