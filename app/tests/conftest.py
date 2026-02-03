import os
import pytest
from fastapi.testclient import TestClient

# Make sure app uses a temp SQLite DB for tests
@pytest.fixture(autouse=True)
def _set_test_db(tmp_path, monkeypatch):
    db_path = tmp_path / "signals_test.sqlite3"
    monkeypatch.setenv("SIGNALS_DB_PATH", str(db_path))
    yield

@pytest.fixture
def client():
    from app.main import app
    return TestClient(app)
