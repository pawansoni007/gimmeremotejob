"""Shared fixtures: persistence on a throwaway SQLite file per test."""

from __future__ import annotations

from pathlib import Path

import pytest

import persistence


@pytest.fixture
async def db(tmp_path: Path):
    """Point persistence at a fresh SQLite database and create the schema."""
    persistence.configure(f"sqlite+aiosqlite:///{tmp_path}/test.db")
    await persistence.create_tables()
    yield
    await persistence.dispose()
