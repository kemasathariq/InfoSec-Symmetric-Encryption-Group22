"""
App settings, read from environment variables or from .env in the repo root.
The app refuses to start when a key is missing, so it never runs on a default key.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
ROOT = BASE_DIR.parent
load_dotenv(ROOT / ".env")  # variables already set in the terminal win over .env


def _required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} is not set. Copy .env.example to .env and fill it in.")
    return value


def _path(name: str, default: Path) -> Path:
    # Relative paths in .env are relative to the repo root, wherever the app is started from.
    p = Path(os.environ.get(name, "").strip() or default)
    return p if p.is_absolute() else ROOT / p


MASTER_KEY = _required("MASTER_KEY")
LOOKUP_KEY = _required("LOOKUP_KEY").encode()
if MASTER_KEY.encode() == LOOKUP_KEY:
    raise RuntimeError("MASTER_KEY and LOOKUP_KEY must be different")

DB_PATH = str(_path("DB_PATH", BASE_DIR / "mbanking.db"))
STORAGE_DIR = _path("STORAGE_DIR", BASE_DIR / "storage")
DEBUG = os.environ.get("FLASK_DEBUG") == "1"