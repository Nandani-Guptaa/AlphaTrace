from app.agent.evaluator import calculate_exposures, evaluate_risk_rules


def test_calculate_exposures_math():
    direct_positions = [
        {"symbol": "NVDA", "exposure": 1800000.0},
        {"symbol": "MSFT", "exposure": 1200000.0}
    ]
    connected_assets = [
        {"correlated_symbol": "AVGO", "correlation": 0.92, "exposure": 3500000.0},
        {"correlated_symbol": "AMD", "correlation": 0.88, "exposure": 1400000.0}
    ]

    exposures = calculate_exposures(direct_positions, connected_assets)
    assert exposures["direct_exposure"] == 3000000.0
    assert exposures["max_single_direct"] == 1800000.0

    # Incremental = (0.92 * 3.5M) + (0.88 * 1.4M) = 3,220,000 + 1,232,000 = 4,452,000
    expected_incremental = (0.92 * 3500000.0) + (0.88 * 1400000.0)
    assert exposures["correlated_incremental"] == round(expected_incremental, 2)
    assert exposures["effective_correlated_exposure"] == round(3000000.0 + expected_incremental, 2)
    assert exposures["cross_strategy_contagion_index"] == 0.92


def test_isolated_pass_vs_graph_breach():
    """Verify that isolated metrics pass but graph correlated exposure causes a critical breach."""
    strategy = {"name": "Quantum Momentum Alpha", "drawdown": 4.2}
    exposures = {
        "direct_exposure": 3000000.0,
        "max_single_direct": 1800000.0,
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
    assert eval_dict["RR-CONTAG-01"].status == "BREACHED"
    assert eval_dict["RR-REGIME-01"].status == "BREACHED"
    assert breaches == 3
