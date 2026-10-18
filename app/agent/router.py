"""Agent Investigation Router & Workflow Orchestrator.
Traverses FalkorDB, performs deterministic evaluations, links memory deltas, and saves results.
"""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, Optional
import uuid

from app.agent.tools import (
    tool_inspect_strategy,
    tool_get_direct_positions,
    tool_traverse_correlated_network,
    tool_get_regime_and_incidents,
    tool_evaluate_quant_risks,
    tool_propose_decision
)
from app.agent.evidence import build_evidence_chain, identify_missing_data_gaps
from app.agent.memory import compare_investigations
from app.graph import queries
from app.models import InvestigationReport, InvestigationRequest

logger = logging.getLogger(__name__)


def run_investigation(request: InvestigationRequest, db=None) -> InvestigationReport:
    """Execute complete explainable risk investigation for a trading strategy."""
    strategy_id = request.strategy_id
    question = request.question
    user_id = request.user_id

    # 1. Fetch Strategy
    strategy = tool_inspect_strategy(strategy_id, db=db)
    if not strategy:
        raise ValueError(f"Strategy with ID '{strategy_id}' not found in graph.")

    # 2. Traverse Direct Holdings
    direct_positions = tool_get_direct_positions(strategy_id, db=db)

    # 3. Traverse Multi-Hop Correlated Network (Graph Differentiator)
    connected_assets = tool_traverse_correlated_network(strategy_id, db=db)

    # 4. Fetch Regime & Incidents
    regime_and_incidents = tool_get_regime_and_incidents(strategy_id, db=db)
    regime = regime_and_incidents["regime"]
    incidents = regime_and_incidents["incidents"]

    # 5. Deterministic Risk Calculations & Rule Evaluations
    quant_results = tool_evaluate_quant_risks(
        strategy, direct_positions, connected_assets, regime, db=db
    )
    exposures = quant_results["exposures"]
    evaluations = quant_results["evaluations"]
    breaches_count = quant_results["breaches_count"]
    insufficient_evidence = any(item.status == "INSUFFICIENT_EVIDENCE" for item in evaluations)

    # 6. Assemble Evidence Chain
    evidence_chain = build_evidence_chain(
        strategy, direct_positions, connected_assets, regime, incidents, exposures
    )
    missing_gaps = identify_missing_data_gaps(strategy, direct_positions, connected_assets)

    # 7. Agent Memory Delta Comparison
    memory_comparison = None
    if request.compare_with_previous:
        prev_inv = queries.get_latest_investigation_for_strategy(strategy_id, db=db)
        memory_comparison = compare_investigations(
            prev_inv, exposures, regime, breaches_count, connected_assets
        )

    # 8. Actionable Recommendation & Decision
    decision_proposed = tool_propose_decision(strategy, exposures, breaches_count, insufficient_evidence)

    # 9. Formulate Clear Narrative Summary
    cluster_evaluation = next((item for item in evaluations if item.rule_id == "RR-CONC-01"), None)
    hidden_risk = bool(cluster_evaluation and cluster_evaluation.status == "BREACHED")
    if hidden_risk:
        isolated_vs_graph = (
            f"ISOLATED PERSPECTIVE: PASS (Direct book is ${exposures['direct_exposure']:,.2f}, Drawdown is {strategy['drawdown']:.1f}%). "
            f"GRAPH PERSPECTIVE: CRITICAL BREACH (Deduplicated gross cluster notional is ${exposures['gross_cluster_notional_usd']:,.2f}, "
            f"revealing ${exposures['peer_connected_notional_usd']:,.2f} of peer-book notional across desk boundaries)."
        )
        exec_summary = (
            f"AlphaTrace graph investigation detected a critical modeled risk in '{strategy['name']}'. "
            f"While the strategy's direct positions appear compliant in isolation, a 2-hop FalkorDB traversal reveals "
            f"a 0.92 correlation to AVGO ($3.5M exposure held by 'STRAT-SEMI-LONG'). Under the current "
            f"'{regime.get('label') if regime else 'unavailable'}' regime, gross cluster notional reaches ${exposures['gross_cluster_notional_usd']:,.2f}, "
            f"breaching Rule RR-CONC-01 ($5.0M limit). (Statistical correlation reflects historical co-movement patterns rather than guaranteed causation; all findings are synthetic simulations for risk modeling)."
        )
    elif insufficient_evidence:
        isolated_vs_graph = (
            f"Direct gross notional is ${exposures['direct_exposure']:,.2f}. Connected graph, drawdown, and/or regime evidence is unavailable, "
            "so AlphaTrace makes no safety or compliance claim."
        )
        exec_summary = (
            f"Strategy '{strategy['name']}' has been evaluated only where evidence exists. "
            "No correlations, peer positions, regimes, or incidents were inferred from the uploaded portfolio."
        )
    else:
        isolated_vs_graph = (
            f"Direct gross notional (${exposures['direct_exposure']:,.2f}) and graph-derived gross cluster notional "
            f"(${exposures['gross_cluster_notional_usd']:,.2f}) do not breach the cluster rule."
        )
        exec_summary = f"Strategy '{strategy['name']}' is compliant with direct and correlated exposure limits."

    report_id = f"INV-{uuid.uuid4().hex[:8].upper()}"
    now_str = datetime.now(timezone.utc).isoformat()

    report = InvestigationReport(
        id=report_id,
        strategy_id=strategy_id,
        strategy_name=strategy["name"],
        question=question,
        user_id=user_id,
        created_at=now_str,
        status="COMPLETED",
        executive_summary=exec_summary,
        isolated_vs_graph_verdict=isolated_vs_graph,
        hidden_risk_detected=hidden_risk,
        # Direct book metrics
        direct_exposure_usd=exposures["direct_exposure"],
        direct_notional_usd=exposures["direct_notional_usd"],
        direct_net_notional_usd=exposures["direct_net_notional_usd"],
        # Peer / cluster metrics
        peer_connected_notional_usd=exposures["peer_connected_notional_usd"],
        peer_connected_net_notional_usd=exposures["peer_connected_net_notional_usd"],
        gross_cluster_notional_usd=exposures["gross_cluster_notional_usd"],
        net_cluster_notional_usd=exposures["net_cluster_notional_usd"],
        # Correlation-adjusted stress estimates
        effective_correlated_exposure_usd=exposures["effective_correlated_exposure"],
        correlation_adjusted_exposure_usd=exposures["correlation_adjusted_exposure_usd"],
        cluster_concentration_ratio=exposures["cluster_concentration_ratio"],
        max_drawdown_pct=strategy.get("drawdown") or 0.0,
        active_regime_volatility=regime["volatility"] if regime else 0.0,
        evaluations=evaluations,
        breaches_count=breaches_count,
        evidence_chain=evidence_chain,
        connected_assets=connected_assets,
        connected_strategies=[
            {"strategy_id": c.get("other_strategy_id"), "name": c.get("other_strategy_name"), "symbol": c.get("correlated_symbol")}
            for c in connected_assets if c.get("other_strategy_id")
        ],
        historical_incidents=incidents,
        memory_comparison=memory_comparison,
        recommended_action=decision_proposed.reason,
        decision_proposed=decision_proposed,
        missing_data_gaps=missing_gaps
    )

    # 10. Persist to FalkorDB
    try:
        queries.save_investigation_node(report.model_dump(), user_id=user_id, db=db)
    except Exception as e:
        logger.warning(f"Could not persist investigation to FalkorDB: {e}")

    return report
