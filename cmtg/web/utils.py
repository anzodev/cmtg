import time
from typing import Callable

import bottle


def sse_response(interval: float = 1.0, retry_ms: int = 1000) -> Callable:
    def outer(f: Callable):
        def inner(*args, **kwargs):
            bottle.response.set_header("Content-Type", "text/event-stream")
            bottle.response.set_header("Cache-Control", "no-cache")
            yield f"retry: {retry_ms}\n"
            for data in f(*args, **kwargs):
                yield f"data: {data}\n\n"
                time.sleep(interval)

        return inner

    return outer


def convert_time(seconds: int) -> str:
    res = ""
    s = seconds % 60
    m = seconds // 60 % 60
    h = seconds // 3600 % 24
    d = seconds // 86400

    res = "".join([res, f"{d}/" if d else ""])
    res = "".join([res, f"{h:0>2}:" if d else f"{h}:"] if h else [])
    res = "".join([res, f"{m:0>2}:" if h else f"{m}:"] if m else [])
    res = "".join([res, f"{s:0>2}" if m else f"{s}s"])
    return res
