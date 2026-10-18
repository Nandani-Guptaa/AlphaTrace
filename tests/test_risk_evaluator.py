from app.agent.evaluator import calculate_exposures, evaluate_risk_rules


def test_calculate_exposures_math():
    direct_positions = [
        {"position_id": "POS-NVDA", "symbol": "NVDA", "exposure": 1800000.0},
        {"position_id": "POS-MSFT", "symbol": "MSFT", "exposure": 1200000.0}
    ]
    connected_assets = [
        {"position_id": "POS-AVGO", "correlated_symbol": "AVGO", "correlation": 0.92, "exposure": 3500000.0},
        {"position_id": "POS-AMD", "correlated_symbol": "AMD", "correlation": 0.88, "exposure": 1400000.0}
    ]

    exposures = calculate_exposures(direct_positions, connected_assets)
    assert exposures["direct_exposure"] == 3000000.0
    assert exposures["max_single_direct"] == 1800000.0
    assert exposures["peer_connected_notional_usd"] == 4900000.0
    assert exposures["gross_cluster_notional_usd"] == 7900000.0

    # Incremental = (0.92 * 3.5M) + (0.88 * 1.4M) = 3,220,000 + 1,232,000 = 4,452,000
    expected_incremental = (0.92 * 3500000.0) + (0.88 * 1400000.0)
    assert exposures["correlated_incremental"] == round(expected_incremental, 2)
    assert exposures["effective_correlated_exposure"] == round(3000000.0 + expected_incremental, 2)
    assert exposures["cross_strategy_contagion_index"] == 0.92


def test_duplicate_paths_and_negative_positions_do_not_inflate_gross_notional():
    exposures = calculate_exposures(
        [{"position_id": "DIRECT-1", "exposure": 100.0}, {"position_id": "HEDGE-1", "exposure": -40.0}],
        [
            {"position_id": "PEER-1", "correlation": 0.8, "exposure": 50.0},
            {"position_id": "PEER-1", "correlation": 0.8, "exposure": 50.0},
            {"position_id": "PEER-2", "correlation": -0.5, "exposure": -20.0},
            {"correlation": 0.9, "exposure": 9999.0},  # Missing stable ID: insufficient evidence, excluded.
        ],
    )
    assert exposures["direct_notional_usd"] == 140.0
    assert exposures["direct_net_notional_usd"] == 60.0
    assert exposures["peer_connected_notional_usd"] == 70.0
    assert exposures["peer_connected_net_notional_usd"] == 30.0
    assert exposures["gross_cluster_notional_usd"] == 210.0
    assert exposures["net_cluster_notional_usd"] == 90.0
    assert exposures["correlation_adjusted_exposure_usd"] == 190.0


def test_no_breach_and_missing_position_evidence_are_distinguished():
    exposures = calculate_exposures(
        [{"position_id": "DIRECT-1", "exposure": 100.0}],
        [{"position_id": "PEER-1", "correlation": 0.2, "exposure": 50.0}, {"correlation": 0.9, "exposure": 999.0}],
    )
    rules = [{"id": "RR-CONC-01", "metric": "Gross cluster", "limit": 200.0, "unit": "USD", "severity": "CRITICAL"}]
    evaluations, breaches = evaluate_risk_rules({"drawdown": 0.0}, exposures, None, rules)
    assert exposures["gross_cluster_notional_usd"] == 150.0
    assert evaluations[0].status == "PASSED"
    assert breaches == 0


def test_custom_portfolio_without_graph_context_is_not_marked_safe():
    exposures = calculate_exposures([{"position_id": "P1", "exposure": 1000.0}], [])
    rules = [
        {"id": "RR-DIR-01", "metric": "Direct", "limit": 2500.0, "unit": "USD", "severity": "HIGH"},
        {"id": "RR-DD-01", "metric": "Drawdown", "limit": 15.0, "unit": "%", "severity": "HIGH"},
        {"id": "RR-CONC-01", "metric": "Cluster", "limit": 5000.0, "unit": "USD", "severity": "CRITICAL"},
        {"id": "RR-CONTAG-01", "metric": "Correlation", "limit": 0.75, "unit": "Ratio", "severity": "HIGH"},
        {"id": "RR-REGIME-01", "metric": "Regime", "limit": 30.0, "unit": "Index", "severity": "MEDIUM"},
    ]
    evaluations, breaches = evaluate_risk_rules({"source": "CUSTOM", "drawdown": None}, exposures, None, rules)
    assert breaches == 0
    assert {item.status for item in evaluations} == {"PASSED", "INSUFFICIENT_EVIDENCE"}
    assert sum(item.status == "INSUFFICIENT_EVIDENCE" for item in evaluations) == 4


def test_isolated_pass_vs_graph_breach():
    """Verify that isolated metrics pass but graph correlated exposure causes a critical breach."""
    strategy = {"name": "Quantum Momentum Alpha", "drawdown": 4.2}
    exposures = {
        "direct_exposure": 3000000.0,
        "max_single_direct": 1800000.0,
        "gross_cluster_notional_usd": 7900000.0,
        "correlated_incremental": 3220000.0,
        "effective_correlated_exposure": 6220000.0,
        "cluster_concentration_ratio": 2.07,
        "cross_strategy_contagion_index": 0.92
    }
    regime = {"label": "High Volatility Dispersion", "volatility": 34.2}
    rules = [
        {"id": "RR-DIR-01", "metric": "Max Single Asset Direct Exposure", "limit": 2500000.0, "unit": "USD", "severity": "HIGH"},
        {"id": "RR-DD-01", "metric": "Strategy Maximum Drawdown", "limit": 15.0, "unit": "Percentage", "severity": "CRITICAL"},
        {"id": "RR-CONC-01", "metric": "Aggregate Correlated Cluster Exposure", "limit": 5000000.0, "unit": "USD", "severity": "CRITICAL"},
        {"id": "RR-CONTAG-01", "metric": "Cross-Strategy Contagion Correlation Index", "limit": 0.75, "unit": "Ratio", "severity": "HIGH"},
        {"id": "RR-REGIME-01", "metric": "Regime Volatility Stress Buffer", "limit": 30.0, "unit": "Volatility Index", "severity": "MEDIUM"}
    ]

    evaluations, breaches = evaluate_risk_rules(strategy, exposures, regime, rules)
    eval_dict = {e.rule_id: e for e in evaluations}

    # Isolated metrics MUST pass
    assert eval_dict["RR-DIR-01"].status == "PASSED"
    assert eval_dict["RR-DD-01"].status == "PASSED"

    # Graph metrics MUST breach
    assert eval_dict["RR-CONC-01"].status == "BREACHED"
    assert eval_dict["RR-CONC-01"].actual_value == 7900000.0
    assert eval_dict["RR-CONTAG-01"].status == "BREACHED"
    assert eval_dict["RR-REGIME-01"].status == "BREACHED"
    assert breaches == 3
