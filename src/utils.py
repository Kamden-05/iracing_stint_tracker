import re

def format_time(seconds: float) -> str:
    h, m = divmod(int(seconds), 3600)
    m, s = divmod(m, 60)
    ms = seconds % 1
    s_with_ms = s + ms
    return f"{h}:{m:02}:{s_with_ms:06.3f}" if h > 0 else f"{m:02}:{s_with_ms:06.3f}"

def get_sheet_id(url: str) -> str:
    match = re.search(r"d/([^/]+)/edit", url)
    print(match.group())
    if match:
        return match.group(1)
    return ""
