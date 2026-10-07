import uuid
from collections.abc import AsyncGenerator
from typing import cast

import pytest
from dishka import AsyncContainer
from dotenv import load_dotenv

from app.application.common.identity_provider import IdentityProvider
from app.presentation.api.bootstrap.persistence_bootstrapper import PersistenceBootstrapper
from tests.integration.di.container import build_test_container

load_dotenv(override=False)
load_dotenv(".env.local", override=False)


@pytest.fixture(scope="session")
def _session_container() -> AsyncContainer:
    return build_test_container()


@pytest.fixture(scope="session")
async def bootstrap_db(_session_container: AsyncContainer) -> None:
    bootstrapper = await _session_container.get(PersistenceBootstrapper)
    await bootstrapper.bootstrap()
    await _session_container.close()


@pytest.fixture
def test_run_suffix() -> str:
    return uuid.uuid4().hex[:12]


@pytest.fixture
async def test_container(bootstrap_db: None) -> AsyncGenerator[AsyncContainer, None]:  # noqa: ARG001
    container = build_test_container()
    async with container() as request_scope:
        yield request_scope


@pytest.fixture
async def test_identity_provider(test_container: AsyncContainer) -> IdentityProvider:
    return cast("IdentityProvider", await test_container.get(IdentityProvider))
