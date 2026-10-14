def test_api_list_strategies(client):
    response = client.get("/api/strategies")
    assert response.status_code == 200
    strats = response.json()
    assert len(strats) >= 4
    strat_ids = [s["id"] for s in strats]
    assert "STRAT-QUANTUM-ALPHA" in strat_ids


def test_api_get_strategy_positions(client):
    response = client.get("/api/strategies/STRAT-QUANTUM-ALPHA/positions")
    assert response.status_code == 200
    positions = response.json()
    assert len(positions) == 2


def test_api_get_strategy_graph_subnetwork(client):
    response = client.get("/api/strategies/STRAT-QUANTUM-ALPHA/graph")
    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "edges" in data
    assert len(data["nodes"]) > 0
    assert len(data["edges"]) > 0


def test_api_investigate_endpoint(client):
    payload = {
        "strategy_id": "STRAT-QUANTUM-ALPHA",
        "question": "Is Strategy A secretly exposed to semiconductor contagion?",
        "user_id": "USR-RISK-LEAD-01",
        "compare_with_previous": True
    }
    response = client.post("/api/investigate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["strategy_id"] == "STRAT-QUANTUM-ALPHA"
    assert data["hidden_risk_detected"] is True
    assert "evaluations" in data
    assert len(data["evaluations"]) >= 4


def test_api_strategy_not_found(client):
    response = client.get("/api/strategies/STRAT-NON-EXISTENT")
    assert response.status_code == 404
