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

    # Compare only values that were actually stored in the prior investigation.
    # A missing field is insufficient evidence, not a reason to invent a baseline.
    prev_stress = prev_data.get("correlation_adjusted_exposure_usd", prev_data.get("effective_correlated_exposure_usd"))
    curr_stress = current_exposures["correlation_adjusted_exposure_usd"]
    if isinstance(prev_stress, (int, float)):
        change_type = "INCREASED" if curr_stress > prev_stress else "DECREASED" if curr_stress < prev_stress else "UNCHANGED"
        deltas.append(InvestigationMemoryDelta(
            field="Correlation-Adjusted Stress Indicator",
            previous_value=f"${prev_stress:,.2f}",
            current_value=f"${curr_stress:,.2f}",
            change_type=change_type,
            significance="HIGH" if prev_stress and abs((curr_stress - prev_stress) / prev_stress) > 0.2 else "MEDIUM"
        ))

    # Prefer the report's saved evidence.  Support the original seeded snapshot
    # field only because it is explicitly persisted in that record.
    prev_peer_gross = prev_data.get("peer_connected_notional_usd", prev_data.get("connected_avgo_exposure_usd"))
    curr_peer_gross = current_exposures["peer_connected_notional_usd"]
    if isinstance(prev_peer_gross, (int, float)):
        deltas.append(InvestigationMemoryDelta(
            field="Peer Connected Gross Notional",
            previous_value=f"${prev_peer_gross:,.2f}",
            current_value=f"${curr_peer_gross:,.2f}",
            change_type="INCREASED" if curr_peer_gross > prev_peer_gross else "DECREASED" if curr_peer_gross < prev_peer_gross else "UNCHANGED",
            significance="HIGH"
        ))

    # 3. Correlation Shift Delta
    prev_corr = prev_data.get("cross_strategy_contagion_index", prev_data.get("correlation_coefficient"))
    curr_corr = current_exposures["cross_strategy_contagion_index"]
    if isinstance(prev_corr, (int, float)):
        deltas.append(InvestigationMemoryDelta(
            field="Peak Cross-Asset Correlation",
            previous_value=f"{prev_corr:.2f}",
            current_value=f"{curr_corr:.2f}",
            change_type="INCREASED" if curr_corr > prev_corr else "DECREASED",
            significance="HIGH"
        ))

    # 4. Regime Volatility Delta
    prev_vol = prev_data.get("active_regime_volatility", prev_data.get("regime_volatility"))
    curr_vol = current_regime.get("volatility", 0.0) if current_regime else 0.0
    if isinstance(prev_vol, (int, float)):
        deltas.append(InvestigationMemoryDelta(
            field="Regime Volatility Index",
            previous_value=f"{prev_vol:.1f}",
            current_value=f"{curr_vol:.1f}",
            change_type="INCREASED" if curr_vol > prev_vol else "DECREASED",
            significance="HIGH" if curr_vol > 30 else "MEDIUM"
        ))

    # 5. Breaches Delta
    prev_breaches = prev_data.get("breaches_count")
    if isinstance(prev_breaches, int):
        deltas.append(InvestigationMemoryDelta(
            field="Active Rule Breaches",
            previous_value=prev_breaches,
            current_value=current_breaches,
            change_type="INCREASED" if current_breaches > prev_breaches else "DECREASED" if current_breaches < prev_breaches else "UNCHANGED",
            significance="HIGH" if current_breaches > prev_breaches else "LOW"
        ))

    # Construct Narrative Delta Summary
    summary = (
        f"Comparison with stored investigation '{previous_inv.get('id')}' ({str(previous_inv.get('created_at', ''))[:10]}). "
        f"Only fields present in both records are shown; omitted metrics are insufficient evidence for a temporal claim."
    )

    return InvestigationComparison(
        previous_investigation_id=previous_inv.get("id"),
        previous_timestamp=previous_inv.get("created_at"),
        deltas=deltas,
        summary=summary
    )
