import pytest
from fastapi.testclient import TestClient

from app.graph.queries import create_custom_strategy
from app.main import app
from app.portfolio import normalize_positions, parse_csv_positions


def test_valid_csv_upload_aggregates_exact_duplicates():
    positions = parse_csv_positions(
        "symbol,quantity,price,asset_type,sector\n"
        "NVDA,10,100,Equity,Technology\n"
        "NVDA,5,100,Equity,Technology\n"
        "TLT,-2,90,ETF,Fixed Income\n"
    )
    assert positions == [
        {"symbol": "NVDA", "price": 100.0, "asset_type": "Equity", "sector": "Technology", "quantity": 15.0, "exposure": 1500.0},
        {"symbol": "TLT", "price": 90.0, "asset_type": "ETF", "sector": "Fixed Income", "quantity": -2.0, "exposure": -180.0},
    ]


@pytest.mark.parametrize("csv_text", ["", "symbol,quantity\nNVDA,1\n", "symbol,quantity,price\n,1,100\n"])
def test_malformed_or_empty_csv_is_rejected(csv_text):
    with pytest.raises(ValueError):
        parse_csv_positions(csv_text)


@pytest.mark.parametrize("rows", [
    [{"symbol": "NVDA", "quantity": 1, "price": 0}],
    [{"symbol": "NVDA", "quantity": 1, "price": "not-a-number"}],
    [{"symbol": "NVDA", "quantity": 0, "price": 100}],
    [{"symbol": "NVDA", "quantity": 1, "price": 100}, {"symbol": "NVDA", "quantity": 1, "price": 101}],
])
def test_invalid_prices_zero_quantity_and_conflicting_duplicates_are_rejected(rows):
    with pytest.raises(ValueError):
        normalize_positions(rows)


class RecordingDb:
    def __init__(self):
        self.calls = []

    def query(self, cypher, params=None):
        self.calls.append((cypher, params or {}))
        return []


def test_custom_strategy_graph_writes_are_isolated_and_parameterized():
    db = RecordingDb()
    positions = normalize_positions([{"symbol": "NVDA", "quantity": 10, "price": 100}])
    first = create_custom_strategy("My book", "USER-A", positions, db=db)
    second = create_custom_strategy("My book", "USER-B", positions, db=db)

    assert first["id"] != second["id"]
    asset_ids = [params["asset_id"] for _, params in db.calls if "asset_id" in params]
    assert len(asset_ids) == 2 and asset_ids[0] != asset_ids[1]
    assert all(all(f"${key}" in cypher for key in params) for cypher, params in db.calls)
    assert all("STRAT-QUANTUM-ALPHA" not in cypher for cypher, _ in db.calls)


def test_custom_portfolio_api_accepts_valid_input_and_rejects_invalid_price(monkeypatch):
    monkeypatch.setattr(
        "app.main.queries.create_custom_strategy",
        lambda **kwargs: {"id": "CUSTOM-TEST", "name": kwargs["strategy_name"], "position_count": len(kwargs["positions"]), "source": "CUSTOM"},
    )
    with TestClient(app) as client:
        created = client.post("/api/custom-portfolios", json={
            "strategy_name": "Upload test", "user_id": "USER-1",
            "positions": [{"symbol": "nvda", "quantity": -2, "price": 100}],
        })
        rejected = client.post("/api/custom-portfolios", json={
            "strategy_name": "Bad", "positions": [{"symbol": "NVDA", "quantity": 1, "price": 0}],
        })
    assert created.status_code == 201
    assert created.json()["id"] == "CUSTOM-TEST"
    assert rejected.status_code == 422
