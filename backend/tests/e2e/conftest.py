import uuid
from collections.abc import AsyncGenerator
from os import getenv
from typing import cast

import pytest
from dishka import AsyncContainer
from dotenv import load_dotenv

from app.application.common.identity_provider import IdentityProvider
from tests.integration.di.container import build_http_ml_test_container

load_dotenv(override=False)
load_dotenv(".env.local", override=False)


@pytest.fixture
def test_run_suffix() -> str:
    return uuid.uuid4().hex[:12]


@pytest.fixture
async def ml_http_container() -> AsyncGenerator[AsyncContainer, None]:
    base_url = getenv("ML_TEST_BASE_URL") or getenv("ML_BASE_URL") or "http://127.0.0.1:8080"
    container = build_http_ml_test_container(
        base_url=base_url,
    )
    async with container() as request_scope:
        yield request_scope


@pytest.fixture
async def ml_http_identity_provider(ml_http_container: AsyncContainer) -> IdentityProvider:
    return cast("IdentityProvider", await ml_http_container.get(IdentityProvider))
