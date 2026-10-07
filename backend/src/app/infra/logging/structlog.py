import logging

import structlog.processors
from structlog.types import Processor


async def build_processors() -> list[Processor]:
    timestamp_processor = structlog.processors.TimeStamper(fmt="iso", utc=True, key="@timestamp")

    processors: list[Processor] = [
        structlog.processors.add_log_level,
        timestamp_processor,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]
    return processors


async def configure_logging() -> None:
    processors = await build_processors()
    formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.processors.JSONRenderer(),
        foreign_pre_chain=processors,
    )

    logging.basicConfig(
        format="%(message)s",
        handlers=[logging.StreamHandler()],
        level=logging.INFO,
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    for foreign_logger in [
        "uvicorn",
        "uvicorn.access",
        "uvicorn.asgi",
        "uvicorn.error",
        "fastapi",
        "custom",
        "httpx",
        "httpcore",
    ]:
        logger = logging.getLogger(foreign_logger)
        logger.handlers = [handler]
        logger.propagate = False

    structlog.configure(
        processors=[*processors, structlog.processors.JSONRenderer()],
        context_class=dict,
        cache_logger_on_first_use=True,
    )
