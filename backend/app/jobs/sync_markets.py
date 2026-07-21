import logging
import sys
import time

from app.db import SessionLocal
from app.services.sync import run_sync

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    once = "--once" in sys.argv
    interval_seconds = 15 * 60

    while True:
        db = SessionLocal()
        try:
            result = run_sync(db)
            logger.info("Sync completed: %s", result)
        except Exception:
            logger.exception("Sync failed")
        finally:
            db.close()

        if once:
            break
        time.sleep(interval_seconds)


if __name__ == "__main__":
    main()
