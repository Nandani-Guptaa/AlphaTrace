from app.graph import queries


def test_get_strategy_by_id(live_graph):
    strat = queries.get_strategy_by_id("STRAT-QUANTUM-ALPHA")
    assert strat is not None
    assert strat["name"] == "Quantum Momentum Alpha"
    assert strat["drawdown"] == 4.2
    assert strat["sharpe"] == 2.15


def test_get_direct_positions(live_graph):
    positions = queries.get_strategy_direct_positions("STRAT-QUANTUM-ALPHA")
    assert len(positions) == 2
    symbols = {p["symbol"] for p in positions}
    assert "NVDA" in symbols
    assert "MSFT" in symbols
    total_exp = sum(p["exposure"] for p in positions)
    assert total_exp == 3000000.0


def test_get_connected_correlated_assets_multihop(live_graph):
    """Verify FalkorDB multi-hop traversal reveals cross-desk correlated assets."""
    connected = queries.get_connected_correlated_assets("STRAT-QUANTUM-ALPHA")
    assert len(connected) > 0
    # Find AVGO connection
    avgo_conn = next((c for c in connected if c["correlated_symbol"] == "AVGO"), None)
    assert avgo_conn is not None
    assert avgo_conn["correlation"] == 0.92
    assert avgo_conn["exposure"] == 3500000.0
    assert avgo_conn["other_strategy_id"] == "STRAT-SEMI-LONG"


def test_get_strategy_market_regime(live_graph):
    regime = queries.get_strategy_market_regime("STRAT-QUANTUM-ALPHA")
    assert regime is not None
    assert regime["label"] == "High Volatility Dispersion"
    assert regime["volatility"] == 34.2


def test_get_strategy_incidents(live_graph):
    incidents = queries.get_strategy_incidents("STRAT-QUANTUM-ALPHA")
    assert len(incidents) >= 1
    assert "INC-2024-TECH-SQUEEZE" in [i["id"] for i in incidents]
