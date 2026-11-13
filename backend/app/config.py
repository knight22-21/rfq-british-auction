from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _flag(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() not in {"0", "false", "no", "off"}


@dataclass(frozen=True)
class Settings:
    database_url: str
    cors_origins: tuple[str, ...]
    seed_demo_data: bool
    sql_echo: bool

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


def load_settings() -> Settings:
    origins = os.getenv(
        "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    )
    default_db = f"sqlite:///{(PROJECT_ROOT / 'auction.db').as_posix()}"
    return Settings(
        database_url=os.getenv("DATABASE_URL", default_db),
        cors_origins=tuple(
            origin.strip() for origin in origins.split(",") if origin.strip()
        ),
        seed_demo_data=_flag("SEED_DEMO_DATA", True),
        sql_echo=_flag("SQL_ECHO", False),
    )


settings = load_settings()
