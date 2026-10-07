from litestar import Router, get
from litestar.response import Response
from litestar.status_codes import HTTP_200_OK

from app.presentation.api.routes.metrics.store import render_prometheus


@get(
    path="/",
    status_code=HTTP_200_OK,
    summary="Prometheus metrics",
)
async def metrics() -> Response[str]:
    content = await render_prometheus()
    return Response(content=content, media_type="text/plain; charset=utf-8")


router = Router(
    path="/metrics",
    route_handlers=[metrics],
    tags=["metrics"],
)
