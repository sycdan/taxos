"""Daily backup scheduler.

Runs the backup once per day at BACKUP_HOUR (default: 2 AM local time).
Designed to run as a long-lived Docker service.
"""

import logging
import os
import time
from datetime import date, datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

TARGET_HOUR = int(os.environ.get("BACKUP_HOUR", "2"))


def main() -> None:
  logger.info(
    "Daily backup scheduler started. Will run at %02d:00 each day.", TARGET_HOUR
  )
  last_run: date | None = None

  while True:
    now = datetime.now()
    if now.hour == TARGET_HOUR and now.date() != last_run:
      logger.info("Starting daily backup...")
      try:
        from taxos.tenant.backup.daily import run

        run()
        last_run = now.date()
      except Exception:
        logger.exception("Daily backup failed")
    time.sleep(60)


if __name__ == "__main__":
  main()
