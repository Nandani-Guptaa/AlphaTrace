from app.agent.router import run_investigation
from app.models import InvestigationRequest


def test_investigate_quantum_alpha():
    """Verify investigation of primary test scenario reveals hidden risk and proposes decision."""
    req = InvestigationRequest(
        strategy_id="STRAT-QUANTUM-ALPHA",
        question="Why is Strategy A risky?",
        user_id="TEST-USER",
        compare_with_previous=True
    )
    report = run_investigation(req)

    assert report.strategy_id == "STRAT-QUANTUM-ALPHA"
    assert report.status == "COMPLETED"
    assert report.hidden_risk_detected is True
    assert report.breaches_count > 0
    assert report.effective_correlated_exposure_usd > report.direct_exposure_usd
    assert report.decision_proposed is not None
    assert report.decision_proposed.action == "REDUCE_OR_HEDGE_EXPOSURE"
    assert len(report.evidence_chain) >= 3


def test_investigate_macro_hedge():
    """Verify macro hedged strategy is clean with zero breaches."""
    req = InvestigationRequest(
        strategy_id="STRAT-MACRO-HEDGE",
        question="Routine check on Macro Hedged book",
        user_id="TEST-USER",
        compare_with_previous=False
    )
    report = run_investigation(req)

    assert report.strategy_id == "STRAT-MACRO-HEDGE"
    assert report.hidden_risk_detected is False
    assert report.breaches_count == 0
    assert report.decision_proposed.action == "APPROVE_CURRENT_ALLOCATION"
