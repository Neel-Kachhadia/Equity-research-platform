"""
backend/tests/conftest.py

Shared pytest configuration and fixtures.
Runs automatically before any test collection.
"""

import os
import sys
from pathlib import Path

# ── Ensure project root is importable ─────────────────────────────────────────
BACKEND_DIR = Path(__file__).parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# ── Load .env before any module imports ───────────────────────────────────────
try:
    from dotenv import load_dotenv
    env_path = BACKEND_DIR / ".env"
    if env_path.exists():
        load_dotenv(env_path, override=False)  # don't override shell env vars
except ImportError:
    pass  # dotenv not installed yet — rely on shell
