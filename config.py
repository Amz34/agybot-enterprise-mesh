"""
AgyBot Mesh - System Configuration & Model Registry
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

PORT = int(os.environ.get("AGYBOT_PORT", "8800"))
HOST = os.environ.get("AGYBOT_HOST", "0.0.0.0")

# Security Token (Can be overridden via env)
SESSION_TOKEN = os.environ.get("AGYBOT_TOKEN", "agy-sovereign-mesh-2026")

# Google Antigravity / Gemini Vertex Settings
GOOGLE_PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT", "project-8c42a42e-60f3-4ca3-8c2")
GOOGLE_LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "global")
GEMINI_MODEL = os.environ.get("AGY_GEMINI_MODEL", "gemini-2.5-flash")

# Execution Engine Bounds
MAX_CLI_TIMEOUT_SECONDS = 60
WORKSPACE_ROOT = Path(os.environ.get("AGYBOT_WORKSPACE", "/home/ubuntu/agy-argon-home/.gemini/antigravity-cli/scratch"))
