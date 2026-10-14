"""Persistent investigation memory and temporal delta comparator.
Detects changes across investigations to explain how compliant strategies deteriorate.
"""

from typing import Any, Dict, List, Optional
from app.models import InvestigationComparison, InvestigationMemoryDelta


def compare_investigations(
    previous_inv: Optional[Dict[str, Any]],
    current_exposures: Dict[str, float],
    current_regime: Optional[Dict[str, Any]],
    current_breaches: int,
    connected_assets: List[Dict[str, Any]]
) -> InvestigationComparison:
    """Compare current investigation metrics with historical graph memory."""
    if not previous_inv or "result_data" not in previous_inv:
        return InvestigationComparison(
            previous_investigation_id=None,
            previous_timestamp=None,
            deltas=[],
            summary="Initial baseline investigation. No previous historical record found for comparison."
        )

    prev_data = previous_inv["result_data"]
    deltas: List[InvestigationMemoryDelta] = []

    # 1. Effective Correlated Exposure Delta
    prev_corr_exp = prev_data.get("effective_correlated_exposure_usd", 0.0)
    curr_corr_exp = current_exposures["effective_correlated_exposure"]
    if prev_corr_exp > 0:
        pct_change = ((curr_corr_exp - prev_corr_exp) / prev_corr_exp) * 100
        change_type = "INCREASED" if curr_corr_exp > prev_corr_exp else "DECREASED"
        deltas.append(InvestigationMemoryDelta(
            field="Effective Correlated Cluster Exposure",
            previous_value=f"${prev_corr_exp:,.2f}",
            current_value=f"${curr_corr_exp:,.2f}",
            change_type=change_type,
            significance="HIGH" if abs(pct_change) > 20 else "MEDIUM"
        ))

    # 2. Peer Connected Asset Delta (AVGO exposure in Strategy B)
    prev_avgo_exp = prev_data.get("connected_avgo_exposure_usd", 1200000.0)
    curr_avgo_exp = next((c["exposure"] for c in connected_assets if c.get("correlated_symbol") == "AVGO"), 0.0)
    if curr_avgo_exp != prev_avgo_exp:
        deltas.append(InvestigationMemoryDelta(
            field="Connected Strategy B (AVGO Exposure)",
            previous_value=f"${prev_avgo_exp:,.2f}",
            current_value=f"${curr_avgo_exp:,.2f}",
            change_type="INCREASED" if curr_avgo_exp > prev_avgo_exp else "DECREASED",
            significance="HIGH"
        ))

    # 3. Correlation Shift Delta
    prev_corr = prev_data.get("correlation_coefficient", 0.72)
    curr_corr = current_exposures["cross_strategy_contagion_index"]
    if curr_corr != prev_corr:
        deltas.append(InvestigationMemoryDelta(
            field="Peak Cross-Asset Correlation",
            previous_value=f"{prev_corr:.2f}",
            current_value=f"{curr_corr:.2f}",
            change_type="INCREASED" if curr_corr > prev_corr else "DECREASED",
            significance="HIGH"
        ))

    # 4. Regime Volatility Delta
    prev_vol = prev_data.get("regime_volatility", 18.5)
    curr_vol = current_regime.get("volatility", 0.0) if current_regime else 0.0
    if curr_vol != prev_vol:
        deltas.append(InvestigationMemoryDelta(
            field="Regime Volatility Index",
            previous_value=f"{prev_vol:.1f}",
            current_value=f"{curr_vol:.1f}",
            change_type="INCREASED" if curr_vol > prev_vol else "DECREASED",
            significance="HIGH" if curr_vol > 30 else "MEDIUM"
        ))

    # 5. Breaches Delta
    prev_breaches = prev_data.get("breaches_count", 0)
    deltas.append(InvestigationMemoryDelta(
        field="Active Rule Breaches",
        previous_value=prev_breaches,
        current_value=current_breaches,
        change_type="INCREASED" if current_breaches > prev_breaches else "UNCHANGED",
        significance="HIGH" if current_breaches > 0 else "LOW"
    ))

    # Construct Narrative Delta Summary
    summary = (
        f"Since investigation '{previous_inv.get('id')}' ({previous_inv.get('created_at')[:10]}), "
        f"peer desk 'STRAT-SEMI-LONG' escalated its AVGO position from ${prev_avgo_exp:,.2f} to ${curr_avgo_exp:,.2f} (+{((curr_avgo_exp - prev_avgo_exp)/max(prev_avgo_exp, 1.0))*100:.1f}%), "
        f"and macro regime volatility rose to {curr_vol:.1f}. This caused the effective cluster exposure to surge from "
        f"${prev_corr_exp:,.2f} to ${curr_corr_exp:,.2f}, flipping the strategy from compliant to {current_breaches} rule breach(es)."
    )

    return InvestigationComparison(
        previous_investigation_id=previous_inv.get("id"),
        previous_timestamp=previous_inv.get("created_at"),
        deltas=deltas,
        summary=summary
    )
