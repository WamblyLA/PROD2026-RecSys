import time

import structlog
from litestar.types import ASGIApp, Receive, Scope, Send

from app.presentation.api.routes.metrics.store import record_request


def metrics_middleware(app: ASGIApp) -> ASGIApp:
    logger = structlog.get_logger("metrics_middleware")

    async def middleware(scope: Scope, receive: Receive, send: Send) -> None:
        if scope.get("type") != "http":  # type: ignore[comparison-overlap]
            await app(scope, receive, send)
            return

        path = scope.get("path", "")
        method = scope.get("method", "")
        start = time.perf_counter()

        status: list[int] = []

        async def send_wrapper(msg: object) -> None:
            msg_dict = msg if isinstance(msg, dict) else {}
            if not status and msg_dict.get("type") == "http.response.start":
                status.append(msg_dict.get("status", 200))
            await send(msg)  # type: ignore[arg-type]

        try:
            await app(scope, receive, send_wrapper)
        finally:
            duration = time.perf_counter() - start
            status_code = status[0] if status else 0
            await record_request(duration, status_code)
            logger.info(
                "Request completed",
                method=method,
                path=path,
                status=status_code,
                duration_seconds=round(duration, 4),
            )

    return middleware
