import random

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15",
]


def get_headers() -> dict[str, str]:
    return {"User-Agent": random.choice(USER_AGENTS)}


def str_like_query(input:str) -> str:
    input = input.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{input}%"
