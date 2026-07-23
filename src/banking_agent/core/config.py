import os
from pathlib import Path
from typing import Literal, cast

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[3]

load_dotenv(PROJECT_ROOT / ".env")

APP_NAME = os.getenv("APP_NAME", "Banking Support Agent")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

WorkflowStorageBackend = Literal["memory", "postgres"]
VALID_WORKFLOW_STORAGE_BACKENDS = {"memory", "postgres"}

raw_workflow_storage_backend = os.getenv(
    "WORKFLOW_STORAGE_BACKEND",
    "memory",
).lower()

if raw_workflow_storage_backend not in VALID_WORKFLOW_STORAGE_BACKENDS:
    raise ValueError(
        "WORKFLOW_STORAGE_BACKEND must be either 'memory' or 'postgres'."
    )

WORKFLOW_STORAGE_BACKEND: WorkflowStorageBackend = cast(
    WorkflowStorageBackend,
    raw_workflow_storage_backend,
)

DATABASE_URL = os.getenv("DATABASE_URL")