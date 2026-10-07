import asyncio

_LOCK = asyncio.Lock()
_state: dict[str, int | float] = {
    "requests_total": 0,
    "errors_total": 0,
    "duration_sum": 0.0,
}


async def record_request(duration_seconds: float, status: int) -> None:
    async with _LOCK:
        _state["requests_total"] = _state["requests_total"] + 1
        _state["duration_sum"] = _state["duration_sum"] + duration_seconds
        if status >= 500:
            _state["errors_total"] = _state["errors_total"] + 1


async def collect() -> tuple[int, int, float]:
    async with _LOCK:
        return (
            int(_state["requests_total"]),
            int(_state["errors_total"]),
            float(_state["duration_sum"]),
        )


async def render_prometheus() -> str:
    requests_total, errors_total, duration_sum = await collect()
    lines = [
        "# HELP http_requests_total Total HTTP requests",
        "# TYPE http_requests_total counter",
        f"http_requests_total {requests_total}",
        "",
        "# HELP http_errors_total Total HTTP 5xx errors",
        "# TYPE http_errors_total counter",
        f"http_errors_total {errors_total}",
        "",
        "# HELP http_request_duration_seconds_total Total request duration in seconds",
        "# TYPE http_request_duration_seconds_total counter",
        f"http_request_duration_seconds_total {duration_sum:.6f}",
    ]
    return "\n".join(lines) + "\n"
