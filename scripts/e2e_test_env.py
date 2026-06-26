"""Bootstrap an isolated SQLite database for E2E audit scripts."""

from __future__ import annotations

import importlib
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def bootstrap_temp_database(*, prefix: str = "e2e_audit") -> Path:
    """Point the app at a fresh temp SQLite file. Call before other app imports."""
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    db_dir = Path(tempfile.mkdtemp(prefix=f"{prefix}_"))
    db_path = db_dir / "test.db"
    os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{db_path.as_posix()}"
    os.environ.setdefault("BOT_TOKEN", "0:E2E_AUDIT_TEST_TOKEN")

    from app.config import get_settings

    get_settings.cache_clear()

    import app.database.session as session_module

    importlib.reload(session_module)
    return db_path


async def init_test_database() -> None:
    from app.database.session import init_db

    await init_db()
