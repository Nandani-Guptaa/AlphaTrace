from app.agent.memory import compare_investigations


def test_compare_investigations_delta_detection():
    previous_inv = {
        "id": "INV-2026-BASE-001",
        "created_at": "2026-10-01T14:00:00Z",
        "result_data": {
            "effective_correlated_exposure_usd": 3860000.0,
            "connected_avgo_exposure_usd": 1200000.0,
            "correlation_coefficient": 0.72,
            "regime_volatility": 18.5,
            "breaches_count": 0
        }
    }

    current_exposures = {
        "direct_exposure": 3000000.0,
        "effective_correlated_exposure": 6220000.0,
        "cross_strategy_contagion_index": 0.92
    }
    current_regime = {"volatility": 34.2}
    current_breaches = 3
    connected_assets = [
        {"correlated_symbol": "AVGO", "exposure": 3500000.0}
    ]

    comp = compare_investigations(
        previous_inv, current_exposures, current_regime, current_breaches, connected_assets
    )

    assert comp.previous_investigation_id == "INV-2026-BASE-001"
    assert len(comp.deltas) >= 4

    delta_fields = {d.field: d for d in comp.deltas}
    assert "Effective Correlated Cluster Exposure" in delta_fields
    assert delta_fields["Effective Correlated Cluster Exposure"].change_type == "INCREASED"

    assert "Connected Strategy B (AVGO Exposure)" in delta_fields
    assert delta_fields["Connected Strategy B (AVGO Exposure)"].change_type == "INCREASED"

    assert "Peak Cross-Asset Correlation" in delta_fields
    assert delta_fields["Peak Cross-Asset Correlation"].change_type == "INCREASED"

    assert "STRAT-SEMI-LONG" in comp.summary
