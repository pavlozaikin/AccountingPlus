"""Database configuration helpers for the AccountingPlus project."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Any


def load_database_config(base_dir: Path) -> Dict[str, Dict[str, Any]]:
    """
    Build the Django DATABASES setting using environment variables.

    Defaults to SQLite stored inside the project directory. For other database
    engines the usual Django environment variables can be provided:
    DJANGO_DB_ENGINE, DJANGO_DB_NAME, DJANGO_DB_USER, DJANGO_DB_PASSWORD,
    DJANGO_DB_HOST, DJANGO_DB_PORT.
    """

    engine = os.environ.get("DJANGO_DB_ENGINE", "django.db.backends.sqlite3")

    if engine == "django.db.backends.sqlite3":
        name: Any = os.environ.get("DJANGO_DB_NAME", base_dir / "db.sqlite3")
    else:
        name = os.environ.get("DJANGO_DB_NAME")
        if not name:
            raise ValueError(
                "Environment variable DJANGO_DB_NAME is required for non-SQLite databases."
            )

    return {
        "default": {
            "ENGINE": engine,
            "NAME": name,
            "USER": os.environ.get("DJANGO_DB_USER", ""),
            "PASSWORD": os.environ.get("DJANGO_DB_PASSWORD", ""),
            "HOST": os.environ.get("DJANGO_DB_HOST", ""),
            "PORT": os.environ.get("DJANGO_DB_PORT", ""),
        }
    }

