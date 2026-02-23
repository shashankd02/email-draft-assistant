from __future__ import annotations

import asyncio

from src.core.config import settings
from src.db.repositories import purge_retention_data
from src.db.session import SessionLocal
from src.utils.logging import get_logger

logger = get_logger("retention_scheduler")


async def retention_scheduler_loop() -> None:
    interval_seconds = max(60, settings.retention_scheduler_interval_minutes * 60)
    while True:
        try:
            with SessionLocal() as db:
                deleted = purge_retention_data(
                    db,
                    drafts_days=settings.retention_drafts_days,
                    transcripts_days=settings.retention_transcripts_days,
                    logs_days=settings.retention_logs_days,
                )
                db.commit()
            logger.info(f"retention_scheduler_deleted={deleted}")
        except Exception as exc:  # pragma: no cover
            logger.error(f"retention_scheduler_error={type(exc).__name__}")
        await asyncio.sleep(interval_seconds)
