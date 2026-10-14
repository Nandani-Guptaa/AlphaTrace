from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ==========================================
# Graph Domain Entity Models
# ==========================================

class Strategy(BaseModel):
    id: str
    name: str
    description: str
    pnl: float
    drawdown: float
    sharpe: float
    updated_at: str


class Asset(BaseModel):
    id: str
    symbol: str
    asset_type: str  # Equity, Crypto, Commodity, FX, Index, Derivative


class Position(BaseModel):
    id: str
    quantity: float
    exposure: float  # In USD
    currency: str = "USD"
    as_of: str


class RiskRule(BaseModel):
    id: str
    metric: str
    limit: float
    unit: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL


class MarketRegime(BaseModel):
    id: str
    label: str
    volatility: float  # Annualized volatility index / VIX equivalent
    as_of: str


class Incident(BaseModel):
    id: str
    description: str
    timestamp: str
    outcome: str


class User(BaseModel):
    id: str
    display_name: str


class Decision(BaseModel):
    id: str
    action: str
    reason: str
    status: str  # PENDING, APPROVED, REJECTED, EXECUTED
    created_at: str


# ==========================================
# Risk Evaluation & Evidence Models
# ==========================================

class RuleEvaluationResult(BaseModel):
    rule_id: str
    metric: str
    limit: float
    unit: str
    actual_value: float
    status: str  # PASSED, WARNING, BREACHED
    severity: str  # INFO, LOW, MEDIUM, HIGH, CRITICAL
    isolated_perspective: str  # What the metric looks like in isolation
    graph_perspective: str  # What the graph traversal reveals
    explanation: str


class EvidenceItem(BaseModel):
    evidence_type: str  # DIRECT_POSITION, CORRELATED_CLUSTER, REGIME_STRESS, HISTORICAL_INCIDENT, CROSS_STRATEGY_OVERLAP
    title: str
    description: str
    data: Dict[str, Any]
    graph_path: Optional[str] = None
    severity: str = "INFO"


class InvestigationMemoryDelta(BaseModel):
    field: str
    previous_value: Any
    current_value: Any
    change_type: str  # INCREASED, DECREASED, NEW, REMOVED, UNCHANGED
    significance: str  # HIGH, MEDIUM, LOW


class InvestigationComparison(BaseModel):
    previous_investigation_id: Optional[str] = None
    previous_timestamp: Optional[str] = None
    deltas: List[InvestigationMemoryDelta] = []
    summary: str = "No previous baseline recorded."


class InvestigationReport(BaseModel):
    id: str
    strategy_id: str
    strategy_name: str
    question: str
    user_id: str
    created_at: str
    status: str  # COMPLETED, FAILED, IN_PROGRESS
    
    # Executive Summary & Differentiator
    executive_summary: str
    isolated_vs_graph_verdict: str
    hidden_risk_detected: bool
    
    # Quantitative Risk Metrics
    direct_exposure_usd: float
    effective_correlated_exposure_usd: float
    cluster_concentration_ratio: float
    max_drawdown_pct: float
    active_regime_volatility: float
    
    # Deterministic Evaluation
    evaluations: List[RuleEvaluationResult]
    breaches_count: int
    
    # Evidence & Traversal Details
    evidence_chain: List[EvidenceItem]
    connected_assets: List[Dict[str, Any]]
    connected_strategies: List[Dict[str, Any]]
    historical_incidents: List[Dict[str, Any]]
    
    # Memory & Change Detection
    memory_comparison: Optional[InvestigationComparison] = None
    
    # Actionable Recommendations
    recommended_action: str
    decision_proposed: Optional[Decision] = None
    missing_data_gaps: List[str] = []


class InvestigationRequest(BaseModel):
    strategy_id: str = "STRAT-QUANTUM-ALPHA"
    question: str = "Why is Strategy A risky and does examining connected positions reveal hidden exposure?"
    user_id: str = "USR-RISK-LEAD-01"
    compare_with_previous: bool = True
