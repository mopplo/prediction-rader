import logging

from alembic import command
from alembic.config import Config

from app.db import SessionLocal
from app.services.sync import run_sync

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate() -> None:
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")


def bootstrap_sync() -> None:
    db = SessionLocal()
    try:
        result = run_sync(db)
        logger.info("Bootstrap sync completed: %s", result)
    finally:
        db.close()


def main() -> None:
    migrate()
    bootstrap_sync()


if __name__ == "__main__":
    main()
