from typing import Literal

from dishka.integrations.litestar import DishkaRouter, FromDishka
from litestar import get
from litestar.response import Response
from litestar.status_codes import HTTP_200_OK, HTTP_503_SERVICE_UNAVAILABLE

from app.presentation.api.bootstrap.readiness_checker import ReadinessChecker


@get(
    path="/health",
    status_code=HTTP_200_OK,
    summary="Liveness probe",
)
async def health() -> dict[Literal["status"], Literal["ok"]]:
    return {"status": "ok"}


@get(
    path="/ready",
    summary="Readiness probe",
)
async def ready(
    readiness_checker: FromDishka[ReadinessChecker],
) -> dict[Literal["status"], Literal["ok", "unavailable"]] | Response[dict[str, str]]:
    if await readiness_checker.check():
        return {"status": "ok"}
    return Response(
        content={"status": "unavailable"},
        status_code=HTTP_503_SERVICE_UNAVAILABLE,
    )


router = DishkaRouter(
    path="/",
    route_handlers=[health, ready],
    tags=["health"],
)
