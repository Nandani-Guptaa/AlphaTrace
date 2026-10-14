import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Ensure root directory is on sys.path
root_dir = Path(__file__).parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from app.main import app
from app.graph.connection import get_db
from app.graph.seed import seed_database


@pytest.fixture(scope="session", autouse=True)
def setup_test_graph():
    """Ensure database schema is indexed and seeded with synthetic test data."""
    db = get_db()
    seed_database(db)
    yield db


@pytest.fixture
def client():
    """FastAPI test client fixture."""
    with TestClient(app) as test_client:
        yield test_client
