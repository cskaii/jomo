"""Regenerate the public API contract without connecting to a hosted database."""
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
# Use a disposable database and do not initialise provider services.
os.environ["APP_ENV"] = "test"
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["DEV_AUTH_ENABLED"] = "false"
os.environ["AI_PRESIDIO_ENABLED"] = "false"
from app.main import app

target = ROOT / "shared/api-contracts/openapi.json"
target.write_text(json.dumps(app.openapi(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"Exported API contract to {target}")
