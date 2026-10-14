"""Agent tools for inspecting strategies, traversing graph paths, evaluating rules, and proposing decisions."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from app.graph import queries
from app.agent.evaluator import calculate_exposures, evaluate_risk_rules
from app.models import Decision


def tool_inspect_strategy(strategy_id: str, db=None) -> Optional[Dict[str, Any]]:
    """Fetch strategy profile from graph."""
    return queries.get_strategy_by_id(strategy_id, db=db)


def tool_get_direct_positions(strategy_id: str, db=None) -> List[Dict[str, Any]]:
    """Traverse direct asset holdings of the strategy."""
    return queries.get_strategy_direct_positions(strategy_id, db=db)


def tool_traverse_correlated_network(strategy_id: str, db=None) -> List[Dict[str, Any]]:
    """Traverse multi-hop relationships to uncover correlated asset exposure across desks."""
    return queries.get_connected_correlated_assets(strategy_id, db=db)


def tool_get_regime_and_incidents(strategy_id: str, db=None) -> Dict[str, Any]:
    """Retrieve macro regime and historical incident precedents."""
    regime = queries.get_strategy_market_regime(strategy_id, db=db)
    incidents = queries.get_strategy_incidents(strategy_id, db=db)
    return {"regime": regime, "incidents": incidents}


def tool_evaluate_quant_risks(
    strategy: Dict[str, Any],
    direct_positions: List[Dict[str, Any]],
    connected_assets: List[Dict[str, Any]],
    regime: Dict[str, Any],
    db=None
) -> Dict[str, Any]:
    """Calculate exposures and evaluate against codified risk rules."""
    exposures = calculate_exposures(direct_positions, connected_assets)
    rules = queries.get_all_risk_rules(db=db)
    evaluations, breaches_count = evaluate_risk_rules(strategy, exposures, regime, rules)
    return {
        "exposures": exposures,
        "evaluations": evaluations,
        "breaches_count": breaches_count
    }


def tool_propose_decision(
    strategy: Dict[str, Any],
    exposures: Dict[str, float],
    breaches_count: int
) -> Decision:
    """Generate deterministic, actionable risk decision based on mathematical findings."""
    dec_id = f"DEC-{uuid.uuid4().hex[:8].upper()}"
    now_str = datetime.now(timezone.utc).isoformat()

    cluster_limit = 5000000.0
    effective_exp = exposures["effective_correlated_exposure"]

    if effective_exp > cluster_limit:
        excess = effective_exp - cluster_limit
        action = "REDUCE_OR_HEDGE_EXPOSURE"
        reason = (
            f"Simulated Risk Suggestion (Non-Execution): Aggregate correlated semiconductor cluster exposure is modeled at "
            f"${effective_exp:,.2f}, exceeding the $5.0M portfolio limit by ${excess:,.2f}. "
            f"(Note: Statistical correlation reflects co-movement under historical regimes, not proof of causation or guaranteed losses. All recommendations are simulated suggestions, not executed trades). "
            f"Suggested simulated adjustments for review: 1) Model trimming direct NVDA exposure by ${excess:,.2f}, or 2) Model short SOXX ETF hedge to offset modeled cross-desk correlation."
        )
        status = "PENDING"
    elif breaches_count > 0:
        action = "FLAG_FOR_MONITORING"
        reason = f"Strategy has {breaches_count} risk rule breach(es) under current market conditions. Increased supervisory monitoring required."
        status = "PENDING"
    else:
        action = "APPROVE_CURRENT_ALLOCATION"
        reason = "Strategy compliant across direct and cross-portfolio correlated exposure parameters."
        status = "APPROVED"

    return Decision(
        id=dec_id,
        action=action,
        reason=reason,
        status=status,
        created_at=now_str
    )
