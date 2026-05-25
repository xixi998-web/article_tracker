from __future__ import annotations

import logging
from typing import Callable

logger = logging.getLogger(__name__)


class LocalScheduler:
    def __init__(self, cron: str = "0 3 * * *", timezone: str = "Asia/Shanghai"):
        self.cron = cron
        self.timezone = timezone

    def start(self, func: Callable, *args, **kwargs) -> None:
        try:
            from apscheduler.schedulers.blocking import BlockingScheduler
            from apscheduler.triggers.cron import CronTrigger
        except ImportError:
            logger.error("apscheduler not installed. Run: pip install apscheduler")
            return

        parts = self.cron.split()
        if len(parts) != 5:
            raise ValueError(f"Invalid cron expression: {self.cron}")

        scheduler = BlockingScheduler(timezone=self.timezone)
        trigger = CronTrigger(
            minute=parts[0], hour=parts[1], day=parts[2],
            month=parts[3], day_of_week=parts[4],
            timezone=self.timezone,
        )
        scheduler.add_job(func, trigger, args=args, kwargs=kwargs)
        logger.info(f"Scheduler started with cron: {self.cron} ({self.timezone})")
        try:
            scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logger.info("Scheduler stopped")
