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


@pytest.fixture(scope="session")
def live_graph():
    """Require the intentionally seeded real FalkorDB graph, or skip integration tests."""
    db = get_db()
    health = db.check_health()
    if health.get("status") != "healthy":
        pytest.skip(f"FalkorDB integration unavailable: {health.get('error', health.get('message'))}")
    if not health.get("node_count"):
        pytest.skip("FalkorDB is reachable but the graph is empty; run scripts/seed_database.py intentionally first.")
    return db


@pytest.fixture
def client(live_graph):
    """FastAPI test client fixture."""
    with TestClient(app) as test_client:
        yield test_client
