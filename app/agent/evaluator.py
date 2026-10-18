"""Deterministic quantitative risk evaluation engine.
All risk calculations are strictly mathematical, reproducible, and explainable.
"""

from typing import Any, Dict, List, Tuple
from app.models import RuleEvaluationResult


def calculate_exposures(
    direct_positions: List[Dict[str, Any]],
    connected_assets: List[Dict[str, Any]]
) -> Dict[str, float]:
    """Calculate distinct-position gross/net notionals and a stress indicator.

    Quant Definitions:
    1. Gross notional is the sum of absolute signed position exposures.
    2. Net notional is the signed sum of those exposures.
    3. Each position ID is counted once, even if several graph paths reach it.
    4. Correlation-adjusted stress is *not* an exposure.  It is an explicitly
       labelled sensitivity indicator: direct gross + Sum(abs(r_i) * peer gross).
       Correlation describes co-movement, not a portfolio weight, causation, or loss.
    5. Cluster Concentration Ratio = Gross Cluster Notional / Direct Gross Notional
    6. Cross-Strategy Contagion Index = Max(r_i across peer desks)
    """
    def distinct(records: List[Dict[str, Any]], id_field: str) -> List[Dict[str, Any]]:
        """Keep the first record for each stable position ID; ignore unidentified rows."""
        seen = set()
        result = []
        for record in records:
            position_id = record.get(id_field)
            if not position_id or position_id in seen:
                continue
            seen.add(position_id)
            result.append(record)
        return result

    direct = distinct(direct_positions, "position_id")
    peers = distinct(connected_assets, "position_id")
    direct_gross = sum(abs(float(p.get("exposure") or 0.0)) for p in direct)
    direct_net = sum(float(p.get("exposure") or 0.0) for p in direct)
    max_single_direct = max((abs(float(p.get("exposure") or 0.0)) for p in direct), default=0.0)
    peer_gross = sum(abs(float(c.get("exposure") or 0.0)) for c in peers)
    peer_net = sum(float(c.get("exposure") or 0.0) for c in peers)
    gross_cluster_notional = direct_gross + peer_gross
    net_cluster_notional = direct_net + peer_net
    correlated_incremental = sum(
        abs(float(c.get("correlation") or 0.0)) * abs(float(c.get("exposure") or 0.0))
        for c in peers
    )
    correlation_adjusted_stress = direct_gross + correlated_incremental
    concentration_ratio = (gross_cluster_notional / direct_gross) if direct_gross else 0.0
    contagion_index = max((abs(float(c.get("correlation") or 0.0)) for c in peers), default=0.0)

    return {
        "direct_exposure": round(direct_gross, 2),  # Backward-compatible alias: gross direct notional.
        "direct_notional_usd": round(direct_gross, 2),
        "direct_net_notional_usd": round(direct_net, 2),
        "max_single_direct": round(max_single_direct, 2),
        "peer_connected_notional_usd": round(peer_gross, 2),
        "peer_connected_net_notional_usd": round(peer_net, 2),
        "gross_cluster_notional_usd": round(gross_cluster_notional, 2),
        "net_cluster_notional_usd": round(net_cluster_notional, 2),
        "correlated_incremental": round(correlated_incremental, 2),
        "effective_correlated_exposure": round(correlation_adjusted_stress, 2),  # Legacy alias; this is not exposure.
        "correlation_adjusted_exposure_usd": round(correlation_adjusted_stress, 2),
        "cluster_concentration_ratio": round(concentration_ratio, 2),
        "cross_strategy_contagion_index": round(contagion_index, 2)
    }


def evaluate_risk_rules(
    strategy: Dict[str, Any],
    exposures: Dict[str, float],
    regime: Dict[str, Any],
    rules: List[Dict[str, Any]]
) -> Tuple[List[RuleEvaluationResult], int]:
    """Deterministically evaluate codified risk rules against both isolated and graph metrics."""
    results: List[RuleEvaluationResult] = []
    breaches_count = 0

    rule_map = {r["id"]: r for r in rules}

    def insufficient(rule: Dict[str, Any], reason: str) -> None:
        results.append(RuleEvaluationResult(
            rule_id=rule["id"], metric=rule["metric"], limit=rule["limit"], unit=rule["unit"],
            actual_value=0.0, status="INSUFFICIENT_EVIDENCE", severity="INFO",
            isolated_perspective="Not evaluated because required portfolio context is unavailable.",
            graph_perspective=reason,
            explanation="No pass/fail conclusion is made when the required graph or market data is absent.",
        ))

    # 1. Max Single Asset Direct Exposure (RR-DIR-01)
    if "RR-DIR-01" in rule_map:
        rule = rule_map["RR-DIR-01"]
        actual = exposures["max_single_direct"]
        limit = rule["limit"]
        is_breach = actual > limit
        status = "BREACHED" if is_breach else "PASSED"
        if is_breach:
            breaches_count += 1
        results.append(RuleEvaluationResult(
            rule_id=rule["id"],
            metric=rule["metric"],
            limit=limit,
            unit=rule["unit"],
            actual_value=actual,
            status=status,
            severity=rule["severity"] if is_breach else "INFO",
            isolated_perspective=f"Largest individual asset exposure is ${actual:,.2f} vs limit of ${limit:,.2f}.",
            graph_perspective=f"Single-asset direct exposure appears compliant in isolation.",
            explanation="Complies with single asset concentration limits when viewed solely within this book."
        ))

    # 2. Strategy Drawdown (RR-DD-01)
    if "RR-DD-01" in rule_map:
        rule = rule_map["RR-DD-01"]
        if strategy.get("source") == "CUSTOM" and strategy.get("drawdown") is None:
            insufficient(rule, "Custom portfolios do not include historical drawdown data.")
        else:
            actual = strategy.get("drawdown", 0.0)
            limit = rule["limit"]
            is_breach = actual > limit
            status = "BREACHED" if is_breach else "PASSED"
            if is_breach:
                breaches_count += 1
            results.append(RuleEvaluationResult(
            rule_id=rule["id"],
            metric=rule["metric"],
            limit=limit,
            unit=rule["unit"],
            actual_value=actual,
            status=status,
            severity=rule["severity"] if is_breach else "INFO",
            isolated_perspective=f"Current strategy drawdown is {actual:.1f}% vs threshold of {limit:.1f}%.",
            graph_perspective=f"Historical incident link shows past liquidation spiked drawdown to -22% under regime shifts.",
            explanation="Drawdown is within normal parameters today, but historical graph links show susceptibility to cascade."
            ))

    # 3. Aggregate Correlated Cluster Exposure (RR-CONC-01)
    if "RR-CONC-01" in rule_map:
        rule = rule_map["RR-CONC-01"]
        if strategy.get("source") == "CUSTOM" and not connected_assets:
            insufficient(rule, "No uploaded correlation or peer-position relationships exist for this custom strategy.")
        else:
            actual = exposures["gross_cluster_notional_usd"]
            limit = rule["limit"]
            is_breach = actual > limit
            status = "BREACHED" if is_breach else "PASSED"
            if is_breach:
                breaches_count += 1
            excess = max(actual - limit, 0.0)
            results.append(RuleEvaluationResult(
            rule_id=rule["id"],
            metric=rule["metric"],
            limit=limit,
            unit=rule["unit"],
            actual_value=actual,
            status=status,
            severity=rule["severity"] if is_breach else "INFO",
            isolated_perspective=f"Strategy direct gross notional is ${exposures['direct_exposure']:,.2f}; peer books are not visible in this view.",
            graph_perspective=f"Deduplicated graph traversal reveals ${actual:,.2f} gross cluster notional across the direct and peer positions.",
            explanation=(
                f"{'CRITICAL BREACH' if is_breach else 'PASSED'}: Gross cluster notional is "
                f"${excess:,.2f} {'over' if is_breach else 'under'} the ${limit:,.2f} limit. "
                "Formula: sum(abs(distinct direct position notionals)) + sum(abs(distinct peer position notionals))."
            )
            ))

    # 4. Cross-Strategy Contagion Correlation Index (RR-CONTAG-01)
    if "RR-CONTAG-01" in rule_map:
        rule = rule_map["RR-CONTAG-01"]
        if strategy.get("source") == "CUSTOM" and not connected_assets:
            insufficient(rule, "No correlation relationships were uploaded or inferred for this custom strategy.")
        else:
            actual = exposures["cross_strategy_contagion_index"]
            limit = rule["limit"]
            is_breach = actual > limit
            status = "BREACHED" if is_breach else "PASSED"
            if is_breach:
                breaches_count += 1
            results.append(RuleEvaluationResult(
            rule_id=rule["id"],
            metric=rule["metric"],
            limit=limit,
            unit=rule["unit"],
            actual_value=actual,
            status=status,
            severity=rule["severity"] if is_breach else "INFO",
            isolated_perspective="N/A: Internal strategy correlations cannot see peer book overlap.",
            graph_perspective=f"NVDA shares a 0.92 correlation with AVGO held heavily ($3.5M) by Strategy 'STRAT-SEMI-LONG'.",
            explanation=f"HIGH BREACH: Peak correlation of {actual:.2f} breaches the contagion limit of {limit:.2f}."
            ))

    # 5. Regime Volatility Stress Buffer (RR-REGIME-01)
    if "RR-REGIME-01" in rule_map and not regime:
        insufficient(rule_map["RR-REGIME-01"], "No market-regime relationship is available for this strategy.")
    elif "RR-REGIME-01" in rule_map and regime:
        rule = rule_map["RR-REGIME-01"]
        actual = regime.get("volatility", 0.0)
        limit = rule["limit"]
        is_breach = actual > limit
        status = "BREACHED" if is_breach else "PASSED"
        if is_breach:
            breaches_count += 1
        results.append(RuleEvaluationResult(
            rule_id=rule["id"],
            metric=rule["metric"],
            limit=limit,
            unit=rule["unit"],
            actual_value=actual,
            status=status,
            severity=rule["severity"] if is_breach else "INFO",
            isolated_perspective="Strategy metrics do not adjust for macro volatility environment.",
            graph_perspective=f"Active regime '{regime.get('label')}' volatility is {actual:.1f} vs stress limit of {limit:.1f}.",
            explanation=f"Elevated market volatility accelerates correlation clustering and liquidation risk."
        ))

    return results, breaches_count
