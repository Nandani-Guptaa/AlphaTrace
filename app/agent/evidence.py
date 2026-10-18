"""Evidence extraction, graph provenance formatting, and data gap identification."""

from typing import Any, Dict, List
from app.models import EvidenceItem


def build_evidence_chain(
    strategy: Dict[str, Any],
    direct_positions: List[Dict[str, Any]],
    connected_assets: List[Dict[str, Any]],
    regime: Dict[str, Any],
    incidents: List[Dict[str, Any]],
    exposures: Dict[str, float]
) -> List[EvidenceItem]:
    """Assemble structured, audit-ready evidence items with explicit graph traversal paths."""
    evidence: List[EvidenceItem] = []

    # 1. Direct Positions
    pos_symbols = [p["symbol"] for p in direct_positions]
    evidence.append(EvidenceItem(
        evidence_type="DIRECT_POSITION",
        title="Direct Strategy Positions",
        description=f"Strategy '{strategy.get('name')}' holds direct positions in {', '.join(pos_symbols)} totalling ${exposures['direct_exposure']:,.2f}.",
        data={
            "direct_positions": direct_positions,
            "total_direct_usd": exposures["direct_exposure"]
        },
        graph_path=f"(:Strategy {{id: '{strategy.get('id')}'}})-[:TRADES]->(:Asset)-[:HAS_POSITION]->(:Position)",
        severity="INFO"
    ))

    # 2. Correlated Contagion Cluster
    high_corr = [c for c in connected_assets if c.get("correlation", 0.0) >= 0.80]
    if high_corr:
        primary = high_corr[0]
        evidence.append(EvidenceItem(
            evidence_type="CORRELATED_CLUSTER",
            title="High Correlated Exposure Across Desks",
            description=(
                f"Asset {primary['direct_symbol']} has a {primary['correlation']:.2f} correlation with "
                f"{primary['correlated_symbol']}, which is held with ${primary['exposure']:,.2f} exposure "
                f"by Strategy '{primary.get('other_strategy_name')}'. Deduplicated gross cluster notional is "
                f"${exposures['gross_cluster_notional_usd']:,.2f}; the separate correlation-adjusted stress indicator is "
                f"${exposures['correlation_adjusted_exposure_usd']:,.2f}."
            ),
            data={
                "correlated_assets": connected_assets,
                "gross_cluster_notional_usd": exposures["gross_cluster_notional_usd"],
                "correlation_adjusted_stress_usd": exposures["correlation_adjusted_exposure_usd"],
                "aggregation_assumption": "Each connected position_id is counted once; correlation is not treated as notional.",
                "concentration_ratio": exposures["cluster_concentration_ratio"]
            },
            graph_path=(
                f"(:Strategy {{id: '{strategy.get('id')}'}})-[:TRADES]->(:Asset {{symbol: '{primary['direct_symbol']}'}})"
                f"-[:CORRELATED_WITH {{coefficient: {primary['correlation']}}}]->(:Asset {{symbol: '{primary['correlated_symbol']}'}})"
                f"<-[:TRADES]-(:Strategy {{id: '{primary.get('other_strategy_id')}'}})"
            ),
            severity="CRITICAL"
        ))

    # 3. Market Regime Stress
    if regime:
        evidence.append(EvidenceItem(
            evidence_type="REGIME_STRESS",
            title=f"Active Market Regime: {regime.get('label')}",
            description=f"Strategy operating during '{regime.get('label')}' with annualized volatility index of {regime.get('volatility'):.1f}.",
            data=regime,
            graph_path=f"(:Strategy {{id: '{strategy.get('id')}'}})-[:ACTIVE_DURING]->(:MarketRegime {{label: '{regime.get('label')}'}})",
            severity="HIGH" if regime.get("volatility", 0.0) > 30.0 else "MEDIUM"
        ))

    # 4. Historical Precedent
    for inc in incidents:
        evidence.append(EvidenceItem(
            evidence_type="HISTORICAL_INCIDENT",
            title=f"Incident Precedent: {inc.get('id')}",
            description=f"{inc.get('description')} Outcome: {inc.get('outcome')}",
            data=inc,
            graph_path=f"(:Strategy {{id: '{strategy.get('id')}'}})-[:EXPERIENCED]->(:Incident {{id: '{inc.get('id')}'}})",
            severity="HIGH"
        ))

    return evidence


def identify_missing_data_gaps(
    strategy: Dict[str, Any],
    direct_positions: List[Dict[str, Any]],
    connected_assets: List[Dict[str, Any]]
) -> List[str]:
    """Highlight required missing data points prior to taking risk-mitigating actions."""
    gaps = [
        "Real-time Prime Broker clearing margin utilization for connected semiconductor positions.",
        "Level-2 order book depth on AVGO and AMD to simulate market impact slippage under rapid liquidation.",
        "Off-exchange OTC options delta hedges currently unmodeled in standard equity graph nodes."
    ]
    return gaps
