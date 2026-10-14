"""Parameterized Cypher queries for AlphaTrace graph traversal.
Zero raw string concatenation ensures Cypher injection immunity.
"""

import json
import logging
from typing import Any, Dict, List, Optional
from app.graph.connection import get_db

logger = logging.getLogger(__name__)


def get_all_strategies(db=None) -> List[Dict[str, Any]]:
    """Retrieve all trading strategies."""
    conn = db or get_db()
    cypher = """
    MATCH (s:Strategy)
    RETURN s.id AS id, s.name AS name, s.description AS description,
           s.pnl AS pnl, s.drawdown AS drawdown, s.sharpe AS sharpe,
           s.updated_at AS updated_at
    ORDER BY s.id
    """
    rows = conn.query(cypher)
    strategies = []
    for r in rows:
        strategies.append({
            "id": r[0],
            "name": r[1],
            "description": r[2],
            "pnl": float(r[3]),
            "drawdown": float(r[4]),
            "sharpe": float(r[5]),
            "updated_at": r[6]
        })
    return strategies


def get_strategy_by_id(strategy_id: str, db=None) -> Optional[Dict[str, Any]]:
    """Retrieve a single strategy by its ID."""
    conn = db or get_db()
    cypher = """
    MATCH (s:Strategy {id: $strategy_id})
    RETURN s.id AS id, s.name AS name, s.description AS description,
           s.pnl AS pnl, s.drawdown AS drawdown, s.sharpe AS sharpe,
           s.updated_at AS updated_at
    """
    rows = conn.query(cypher, {"strategy_id": strategy_id})
    if not rows:
        return None
    r = rows[0]
    return {
        "id": r[0],
        "name": r[1],
        "description": r[2],
        "pnl": float(r[3]),
        "drawdown": float(r[4]),
        "sharpe": float(r[5]),
        "updated_at": r[6]
    }


def get_strategy_direct_positions(strategy_id: str, db=None) -> List[Dict[str, Any]]:
    """Get direct assets and positions held by a strategy.
    Traverses: Strategy -> TRADES -> Asset -> HAS_POSITION -> Position
    """
    conn = db or get_db()
    cypher = """
    MATCH (s:Strategy {id: $strategy_id})-[:TRADES]->(a:Asset)-[:HAS_POSITION]->(p:Position)
    RETURN a.id AS asset_id, a.symbol AS symbol, a.asset_type AS asset_type,
           p.id AS position_id, p.quantity AS quantity, p.exposure AS exposure,
           p.currency AS currency, p.as_of AS as_of
    ORDER BY p.exposure DESC
    """
    rows = conn.query(cypher, {"strategy_id": strategy_id})
    positions = []
    for r in rows:
        positions.append({
            "asset_id": r[0],
            "symbol": r[1],
            "asset_type": r[2],
            "position_id": r[3],
            "quantity": float(r[4]),
            "exposure": float(r[5]),
            "currency": r[6],
            "as_of": r[7]
        })
    return positions


def get_connected_correlated_assets(strategy_id: str, db=None) -> List[Dict[str, Any]]:
    """Traverse graph relationships to discover connected, correlated assets held across the firm.
    Traverses:
    (TargetStrategy)-[:TRADES]->(TradedAsset)-[rel:CORRELATED_WITH]->(CorrelatedAsset)
    <-[:TRADES]-(OtherStrategy), (CorrelatedAsset)-[:HAS_POSITION]->(OtherPosition)
    """
    conn = db or get_db()
    cypher = """
    MATCH (s:Strategy {id: $strategy_id})-[:TRADES]->(directAsset:Asset)-[c:CORRELATED_WITH]->(corrAsset:Asset)
    OPTIONAL MATCH (corrAsset)-[:HAS_POSITION]->(pos:Position)
    OPTIONAL MATCH (otherStrat:Strategy)-[:TRADES]->(corrAsset)
    WHERE otherStrat.id <> $strategy_id
    RETURN directAsset.symbol AS direct_symbol,
           corrAsset.symbol AS correlated_symbol,
           corrAsset.asset_type AS correlated_type,
           c.coefficient AS correlation,
           c.regime AS correlation_regime,
           pos.id AS position_id,
           pos.exposure AS exposure,
           otherStrat.id AS other_strategy_id,
           otherStrat.name AS other_strategy_name
    ORDER BY c.coefficient DESC, pos.exposure DESC
    """
    rows = conn.query(cypher, {"strategy_id": strategy_id})
    connected = []
    for r in rows:
        connected.append({
            "direct_symbol": r[0],
            "correlated_symbol": r[1],
            "correlated_type": r[2],
            "correlation": float(r[3]) if r[3] is not None else 0.0,
            "correlation_regime": r[4] or "Normal",
            "position_id": r[5],
            "exposure": float(r[6]) if r[6] is not None else 0.0,
            "other_strategy_id": r[7],
            "other_strategy_name": r[8]
        })
    return connected


def get_strategy_market_regime(strategy_id: str, db=None) -> Optional[Dict[str, Any]]:
    """Retrieve active market regime connected to a strategy."""
    conn = db or get_db()
    cypher = """
    MATCH (s:Strategy {id: $strategy_id})-[:ACTIVE_DURING]->(m:MarketRegime)
    RETURN m.id AS id, m.label AS label, m.volatility AS volatility, m.as_of AS as_of
    LIMIT 1
    """
    rows = conn.query(cypher, {"strategy_id": strategy_id})
    if not rows:
        return None
    r = rows[0]
    return {
        "id": r[0],
        "label": r[1],
        "volatility": float(r[2]),
        "as_of": r[3]
    }


def get_strategy_incidents(strategy_id: str, db=None) -> List[Dict[str, Any]]:
    """Retrieve historical incidents experienced by a strategy or connected strategies."""
    conn = db or get_db()
    cypher = """
    MATCH (s:Strategy {id: $strategy_id})-[:EXPERIENCED]->(i:Incident)
    RETURN i.id AS id, i.description AS description, i.timestamp AS timestamp, i.outcome AS outcome
    """
    rows = conn.query(cypher, {"strategy_id": strategy_id})
    incidents = []
    for r in rows:
        incidents.append({
            "id": r[0],
            "description": r[1],
            "timestamp": r[2],
            "outcome": r[3]
        })
    return incidents


def get_all_risk_rules(db=None) -> List[Dict[str, Any]]:
    """Retrieve all codified risk rules."""
    conn = db or get_db()
    cypher = """
    MATCH (r:RiskRule)
    RETURN r.id AS id, r.metric AS metric, r.limit AS limit, r.unit AS unit, r.severity AS severity
    ORDER BY r.id
    """
    rows = conn.query(cypher)
    rules = []
    for r in rows:
        rules.append({
            "id": r[0],
            "metric": r[1],
            "limit": float(r[2]),
            "unit": r[3],
            "severity": r[4]
        })
    return rules


def get_latest_investigation_for_strategy(strategy_id: str, db=None) -> Optional[Dict[str, Any]]:
    """Retrieve the most recent historical investigation for strategy memory delta evaluation."""
    conn = db or get_db()
    cypher = """
    MATCH (inv:Investigation {strategy_id: $strategy_id})
    RETURN inv.id AS id, inv.user_id AS user_id, inv.question AS question,
           inv.created_at AS created_at, inv.status AS status, inv.result_json AS result_json
    ORDER BY inv.created_at DESC
    LIMIT 1
    """
    rows = conn.query(cypher, {"strategy_id": strategy_id})
    if not rows:
        return None
    r = rows[0]
    result_data = {}
    if r[5]:
        try:
            result_data = json.loads(r[5])
        except Exception:
            result_data = {"raw": r[5]}

    return {
        "id": r[0],
        "user_id": r[1],
        "question": r[2],
        "created_at": r[3],
        "status": r[4],
        "result_data": result_data
    }


def save_investigation_node(report_dict: Dict[str, Any], user_id: str = "USR-RISK-LEAD-01", db=None) -> str:
    """Save investigation run and link to Strategy and Decision in FalkorDB."""
    conn = db or get_db()
    inv_id = report_dict["id"]
    strategy_id = report_dict["strategy_id"]
    question = report_dict["question"]
    created_at = report_dict["created_at"]
    status = report_dict["status"]
    result_json = json.dumps(report_dict)

    # Create investigation node
    cypher_inv = """
    MERGE (inv:Investigation {id: $id})
    SET inv.strategy_id = $strategy_id,
        inv.user_id = $user_id,
        inv.question = $question,
        inv.created_at = $created_at,
        inv.status = $status,
        inv.result_json = $result_json
    """
    conn.query(cypher_inv, {
        "id": inv_id,
        "strategy_id": strategy_id,
        "user_id": user_id,
        "question": question,
        "created_at": created_at,
        "status": status,
        "result_json": result_json
    })

    # Link User -> Investigation and Investigation -> Strategy
    conn.query(
        """
        MATCH (u:User {id: $user_id}), (inv:Investigation {id: $inv_id})
        MERGE (u)-[:RAN]->(inv)
        """,
        {"user_id": user_id, "inv_id": inv_id}
    )

    conn.query(
        """
        MATCH (inv:Investigation {id: $inv_id}), (s:Strategy {id: $strategy_id})
        MERGE (inv)-[:INVESTIGATED]->(s)
        """,
        {"inv_id": inv_id, "strategy_id": strategy_id}
    )

    # If decision proposed, create Decision node and link
    if report_dict.get("decision_proposed"):
        dec = report_dict["decision_proposed"]
        conn.query(
            """
            MERGE (d:Decision {id: $id})
            SET d.action = $action,
                d.reason = $reason,
                d.status = $status,
                d.created_at = $created_at
            """,
            {
                "id": dec["id"],
                "action": dec["action"],
                "reason": dec["reason"],
                "status": dec["status"],
                "created_at": dec["created_at"]
            }
        )
        conn.query(
            """
            MATCH (inv:Investigation {id: $inv_id}), (d:Decision {id: $dec_id})
            MERGE (inv)-[:RESULTED_IN]->(d)
            """,
            {"inv_id": inv_id, "dec_id": dec["id"]}
        )

    return inv_id


def get_all_investigations(limit: int = 20, db=None) -> List[Dict[str, Any]]:
    """Retrieve history of investigations."""
    conn = db or get_db()
    cypher = """
    MATCH (inv:Investigation)
    RETURN inv.id AS id, inv.strategy_id AS strategy_id, inv.user_id AS user_id,
           inv.question AS question, inv.created_at AS created_at, inv.status AS status,
           inv.result_json AS result_json
    ORDER BY inv.created_at DESC
    LIMIT $limit
    """
    rows = conn.query(cypher, {"limit": limit})
    history = []
    for r in rows:
        res_data = {}
        if r[6]:
            try:
                res_data = json.loads(r[6])
            except Exception:
                res_data = {}
        history.append({
            "id": r[0],
            "strategy_id": r[1],
            "user_id": r[2],
            "question": r[3],
            "created_at": r[4],
            "status": r[5],
            "result_summary": res_data.get("executive_summary", "")
        })
    return history


def get_investigation_by_id(investigation_id: str, db=None) -> Optional[Dict[str, Any]]:
    """Retrieve a single investigation by ID from FalkorDB."""
    conn = db or get_db()
    cypher = """
    MATCH (inv:Investigation {id: $investigation_id})
    RETURN inv.id AS id, inv.strategy_id AS strategy_id, inv.user_id AS user_id,
           inv.question AS question, inv.created_at AS created_at, inv.status AS status,
           inv.result_json AS result_json
    """
    rows = conn.query(cypher, {"investigation_id": investigation_id})
    if not rows:
        return None
    r = rows[0]
    result_data = {}
    if r[6]:
        try:
            result_data = json.loads(r[6])
        except Exception:
            result_data = {"raw": r[6]}

    return {
        "id": r[0],
        "strategy_id": r[1],
        "user_id": r[2],
        "question": r[3],
        "created_at": r[4],
        "status": r[5],
        "result_data": result_data
    }

