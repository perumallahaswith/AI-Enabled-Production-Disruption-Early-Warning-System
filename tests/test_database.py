"""Test suite for database initialization and connectivity."""

import pytest
from app.database import engine, check_db_connection, init_db, SessionLocal
from app.models.base import FabModelBase
from sqlalchemy import text


def test_database_connection():
    """Verify database connection succeeds."""
    assert check_db_connection() is True


def test_database_session():
    """Verify session creation and raw query execution."""
    db = SessionLocal()
    try:
        result = db.execute(text("SELECT 1")).scalar()
        assert result == 1
    finally:
        db.close()


def test_init_db():
    """Verify table creation runs without error."""
    init_db()
    assert check_db_connection() is True
