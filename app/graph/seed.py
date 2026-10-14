"""Seed script for AlphaTrace graph database.
Populates realistic synthetic trading risk data demonstrating:
1. Strategy-level isolation vs Graph-traversed contagion
2. Hidden cross-strategy correlated concentration
3. Regime shifts and historical incident precedent
4. Historical investigation baseline for agent memory comparison
"""

import json
import logging
from typing import Any, Dict
from app.graph.connection import get_db
from app.graph.schema import init_schema

logger = logging.getLogger(__name__)


def seed_database(graph_conn=None) -> Dict[str, Any]:
    """Wipes and seeds the graph database with synthetic test scenario data."""
    db = graph_conn or get_db()
    graph = db.get_graph()

    logger.info("Initializing schema indices...")
    init_schema(db)

    logger.info("Clearing previous graph contents...")
    try:
        # Delete all nodes and relationships
        db.query("MATCH (n) DETACH DELETE n")
    except Exception as e:
        logger.warning(f"Could not clear graph (might be empty): {e}")

    # 1. Create Strategies
    strategies = [
        {
            "id": "STRAT-QUANTUM-ALPHA",
            "name": "Quantum Momentum Alpha",
            "description": "High-frequency momentum and statistical equity arbitrage focused on large-cap tech.",
            "pnl": 420000.0,
            "drawdown": 4.2,  # isolated looks healthy (<15%)
            "sharpe": 2.15,
            "updated_at": "2026-10-14T10:00:00Z"
        },
        {
            "id": "STRAT-SEMI-LONG",
            "name": "Semiconductor Long-Bias",
            "description": "Long-focused fundamental growth strategy in semiconductor hardware & fabrication.",
            "pnl": 890000.0,
            "drawdown": 8.5,
            "sharpe": 1.78,
            "updated_at": "2026-10-14T09:30:00Z"
        },
        {
            "id": "STRAT-TECH-FACTOR",
            "name": "Tech Factor Neutral",
            "description": "Systematic factor equity desk trading mega-cap technology pairs.",
            "pnl": 150000.0,
            "drawdown": 3.1,
            "sharpe": 1.95,
            "updated_at": "2026-10-14T11:15:00Z"
        },
        {
            "id": "STRAT-MACRO-HEDGE",
            "name": "Macro Hedged Diversified",
            "description": "Cross-asset multi-strategy book with hedged treasury and index positions.",
            "pnl": 310000.0,
            "drawdown": 2.4,
            "sharpe": 2.40,
            "updated_at": "2026-10-14T10:45:00Z"
        }
    ]

    for s in strategies:
        db.query(
            """
            CREATE (s:Strategy {
                id: $id,
                name: $name,
                description: $description,
                pnl: $pnl,
                drawdown: $drawdown,
                sharpe: $sharpe,
                updated_at: $updated_at
            })
            """,
            s
        )

    # 2. Create Assets
    assets = [
        {"id": "ASSET-NVDA", "symbol": "NVDA", "asset_type": "Equity"},
        {"id": "ASSET-MSFT", "symbol": "MSFT", "asset_type": "Equity"},
        {"id": "ASSET-AVGO", "symbol": "AVGO", "asset_type": "Equity"},
        {"id": "ASSET-AMD", "symbol": "AMD", "asset_type": "Equity"},
        {"id": "ASSET-SOXX", "symbol": "SOXX", "asset_type": "Index ETF"},
        {"id": "ASSET-TLT", "symbol": "TLT", "asset_type": "Fixed Income ETF"},
        {"id": "ASSET-GLD", "symbol": "GLD", "asset_type": "Commodity ETF"}
    ]

    for a in assets:
        db.query(
            "CREATE (a:Asset {id: $id, symbol: $symbol, asset_type: $asset_type})",
            a
        )

    # 3. Create Positions
    positions = [
        {"id": "POS-NVDA-QUANTUM", "quantity": 15000.0, "exposure": 1800000.0, "currency": "USD", "as_of": "2026-10-14T10:00:00Z"},
        {"id": "POS-MSFT-QUANTUM", "quantity": 2800.0, "exposure": 1200000.0, "currency": "USD", "as_of": "2026-10-14T10:00:00Z"},
        {"id": "POS-AVGO-SEMI", "quantity": 2200.0, "exposure": 3500000.0, "currency": "USD", "as_of": "2026-10-14T09:30:00Z"},
        {"id": "POS-AMD-FACTOR", "quantity": 9000.0, "exposure": 1400000.0, "currency": "USD", "as_of": "2026-10-14T11:15:00Z"},
        {"id": "POS-TLT-MACRO", "quantity": 20000.0, "exposure": 1900000.0, "currency": "USD", "as_of": "2026-10-14T10:45:00Z"},
        {"id": "POS-GLD-MACRO", "quantity": 8000.0, "exposure": 1600000.0, "currency": "USD", "as_of": "2026-10-14T10:45:00Z"}
    ]

    for p in positions:
        db.query(
            """
            CREATE (p:Position {
                id: $id,
                quantity: $quantity,
                exposure: $exposure,
                currency: $currency,
                as_of: $as_of
            })
            """,
            p
        )

    # 4. Create Risk Rules
    risk_rules = [
        {
            "id": "RR-DIR-01",
            "metric": "Max Single Asset Direct Exposure",
            "limit": 2500000.0,
            "unit": "USD",
            "severity": "HIGH"
        },
        {
            "id": "RR-DD-01",
            "metric": "Strategy Maximum Drawdown",
            "limit": 15.0,
            "unit": "Percentage",
            "severity": "CRITICAL"
        },
        {
            "id": "RR-CONC-01",
            "metric": "Aggregate Correlated Cluster Exposure",
            "limit": 5000000.0,
            "unit": "USD",
            "severity": "CRITICAL"
        },
        {
            "id": "RR-CONTAG-01",
            "metric": "Cross-Strategy Contagion Correlation Index",
            "limit": 0.75,
            "unit": "Ratio",
            "severity": "HIGH"
        },
        {
            "id": "RR-REGIME-01",
            "metric": "Regime Volatility Stress Buffer",
            "limit": 30.0,
            "unit": "Volatility Index",
            "severity": "MEDIUM"
        }
    ]

    for r in risk_rules:
        db.query(
            """
            CREATE (r:RiskRule {
                id: $id,
                metric: $metric,
                limit: $limit,
                unit: $unit,
                severity: $severity
            })
            """,
            r
        )

    # 5. Create Market Regimes
    regimes = [
        {
            "id": "REGIME-HIGH-VOL",
            "label": "High Volatility Dispersion",
            "volatility": 34.2,
            "as_of": "2026-10-14T08:00:00Z"
        },
        {
            "id": "REGIME-LOW-VOL",
            "label": "Low Volatility Expansion",
            "volatility": 14.8,
            "as_of": "2026-09-01T08:00:00Z"
        }
    ]

    for reg in regimes:
        db.query(
            """
            CREATE (m:MarketRegime {
                id: $id,
                label: $label,
                volatility: $volatility,
                as_of: $as_of
            })
            """,
            reg
        )

    # 6. Create Historical Incidents
    incidents = [
        {
            "id": "INC-2024-TECH-SQUEEZE",
            "description": "Tech Earnings Squeeze & Unhedged Cross-Desk Cascade: Correlated semiconductor positions triggered simultaneous broker margin calls.",
            "timestamp": "2024-07-24T16:00:00Z",
            "outcome": "Forced liquidation of $4.8M across connected tech strategies; drawdown accelerated to -22% within 48h."
        },
        {
            "id": "INC-2023-RATES-SHOCK",
            "description": "Federal Reserve Rate Surprise: Bond yield spike causing rapid growth stock multiple compression.",
            "timestamp": "2023-10-19T14:30:00Z",
            "outcome": "Drawdown contained via stop-loss execution; portfolio de-risked by 30%."
        }
    ]

    for inc in incidents:
        db.query(
            """
            CREATE (i:Incident {
                id: $id,
                description: $description,
                timestamp: $timestamp,
                outcome: $outcome
            })
            """,
            inc
        )

    # 7. Create Users
    users = [
        {"id": "USR-RISK-LEAD-01", "display_name": "Chief Risk Officer (Sarah Vance)"},
        {"id": "USR-ANALYST-02", "display_name": "Senior Quant Analyst (Marcus Sterling)"}
    ]

    for u in users:
        db.query("CREATE (u:User {id: $id, display_name: $display_name})", u)

    # 8. Create Relationships
    # Strategy -> Asset (TRADES)
    db.query("MATCH (s:Strategy {id: 'STRAT-QUANTUM-ALPHA'}), (a:Asset {id: 'ASSET-NVDA'}) CREATE (s)-[:TRADES]->(a)")
    db.query("MATCH (s:Strategy {id: 'STRAT-QUANTUM-ALPHA'}), (a:Asset {id: 'ASSET-MSFT'}) CREATE (s)-[:TRADES]->(a)")
    db.query("MATCH (s:Strategy {id: 'STRAT-SEMI-LONG'}), (a:Asset {id: 'ASSET-AVGO'}) CREATE (s)-[:TRADES]->(a)")
    db.query("MATCH (s:Strategy {id: 'STRAT-TECH-FACTOR'}), (a:Asset {id: 'ASSET-AMD'}) CREATE (s)-[:TRADES]->(a)")
    db.query("MATCH (s:Strategy {id: 'STRAT-MACRO-HEDGE'}), (a:Asset {id: 'ASSET-TLT'}) CREATE (s)-[:TRADES]->(a)")
    db.query("MATCH (s:Strategy {id: 'STRAT-MACRO-HEDGE'}), (a:Asset {id: 'ASSET-GLD'}) CREATE (s)-[:TRADES]->(a)")

    # Asset -> Position (HAS_POSITION)
    db.query("MATCH (a:Asset {id: 'ASSET-NVDA'}), (p:Position {id: 'POS-NVDA-QUANTUM'}) CREATE (a)-[:HAS_POSITION]->(p)")
    db.query("MATCH (a:Asset {id: 'ASSET-MSFT'}), (p:Position {id: 'POS-MSFT-QUANTUM'}) CREATE (a)-[:HAS_POSITION]->(p)")
    db.query("MATCH (a:Asset {id: 'ASSET-AVGO'}), (p:Position {id: 'POS-AVGO-SEMI'}) CREATE (a)-[:HAS_POSITION]->(p)")
    db.query("MATCH (a:Asset {id: 'ASSET-AMD'}), (p:Position {id: 'POS-AMD-FACTOR'}) CREATE (a)-[:HAS_POSITION]->(p)")
    db.query("MATCH (a:Asset {id: 'ASSET-TLT'}), (p:Position {id: 'POS-TLT-MACRO'}) CREATE (a)-[:HAS_POSITION]->(p)")
    db.query("MATCH (a:Asset {id: 'ASSET-GLD'}), (p:Position {id: 'POS-GLD-MACRO'}) CREATE (a)-[:HAS_POSITION]->(p)")

    # Asset -> Asset (CORRELATED_WITH)
    # The key graph link: NVDA is correlated with AVGO (0.92) and AMD (0.88)
    db.query("MATCH (a1:Asset {id: 'ASSET-NVDA'}), (a2:Asset {id: 'ASSET-AVGO'}) CREATE (a1)-[:CORRELATED_WITH {coefficient: 0.92, regime: 'High Volatility Dispersion'}]->(a2)")
    db.query("MATCH (a2:Asset {id: 'ASSET-AVGO'}), (a1:Asset {id: 'ASSET-NVDA'}) CREATE (a2)-[:CORRELATED_WITH {coefficient: 0.92, regime: 'High Volatility Dispersion'}]->(a1)")

    db.query("MATCH (a1:Asset {id: 'ASSET-NVDA'}), (a2:Asset {id: 'ASSET-AMD'}) CREATE (a1)-[:CORRELATED_WITH {coefficient: 0.88, regime: 'High Volatility Dispersion'}]->(a2)")
    db.query("MATCH (a2:Asset {id: 'ASSET-AMD'}), (a1:Asset {id: 'ASSET-NVDA'}) CREATE (a2)-[:CORRELATED_WITH {coefficient: 0.88, regime: 'High Volatility Dispersion'}]->(a1)")

    db.query("MATCH (a1:Asset {id: 'ASSET-NVDA'}), (a2:Asset {id: 'ASSET-SOXX'}) CREATE (a1)-[:CORRELATED_WITH {coefficient: 0.85, regime: 'High Volatility Dispersion'}]->(a2)")
    db.query("MATCH (a1:Asset {id: 'ASSET-AVGO'}), (a2:Asset {id: 'ASSET-SOXX'}) CREATE (a1)-[:CORRELATED_WITH {coefficient: 0.89, regime: 'High Volatility Dispersion'}]->(a2)")

    # Position -> RiskRule (SUBJECT_TO)
    db.query("MATCH (p:Position {id: 'POS-NVDA-QUANTUM'}), (r:RiskRule {id: 'RR-DIR-01'}) CREATE (p)-[:SUBJECT_TO]->(r)")
    db.query("MATCH (p:Position {id: 'POS-MSFT-QUANTUM'}), (r:RiskRule {id: 'RR-DIR-01'}) CREATE (p)-[:SUBJECT_TO]->(r)")
    db.query("MATCH (p:Position {id: 'POS-AVGO-SEMI'}), (r:RiskRule {id: 'RR-DIR-01'}) CREATE (p)-[:SUBJECT_TO]->(r)")
    db.query("MATCH (p:Position {id: 'POS-AMD-FACTOR'}), (r:RiskRule {id: 'RR-DIR-01'}) CREATE (p)-[:SUBJECT_TO]->(r)")

    # Strategy -> MarketRegime (ACTIVE_DURING)
    db.query("MATCH (s:Strategy {id: 'STRAT-QUANTUM-ALPHA'}), (m:MarketRegime {id: 'REGIME-HIGH-VOL'}) CREATE (s)-[:ACTIVE_DURING]->(m)")
    db.query("MATCH (s:Strategy {id: 'STRAT-SEMI-LONG'}), (m:MarketRegime {id: 'REGIME-HIGH-VOL'}) CREATE (s)-[:ACTIVE_DURING]->(m)")
    db.query("MATCH (s:Strategy {id: 'STRAT-TECH-FACTOR'}), (m:MarketRegime {id: 'REGIME-HIGH-VOL'}) CREATE (s)-[:ACTIVE_DURING]->(m)")
    db.query("MATCH (s:Strategy {id: 'STRAT-MACRO-HEDGE'}), (m:MarketRegime {id: 'REGIME-LOW-VOL'}) CREATE (s)-[:ACTIVE_DURING]->(m)")

    # Strategy -> Incident (EXPERIENCED)
    db.query("MATCH (s:Strategy {id: 'STRAT-QUANTUM-ALPHA'}), (i:Incident {id: 'INC-2024-TECH-SQUEEZE'}) CREATE (s)-[:EXPERIENCED]->(i)")
    db.query("MATCH (s:Strategy {id: 'STRAT-SEMI-LONG'}), (i:Incident {id: 'INC-2024-TECH-SQUEEZE'}) CREATE (s)-[:EXPERIENCED]->(i)")

    # 9. Create Historical Baseline Investigation for Agent Memory
    baseline_result = {
        "strategy_id": "STRAT-QUANTUM-ALPHA",
        "created_at": "2026-10-01T14:00:00Z",
        "direct_exposure_usd": 3000000.0,
        "effective_correlated_exposure_usd": 3860000.0,
        "connected_avgo_exposure_usd": 1200000.0,
        "correlation_coefficient": 0.72,
        "breaches_count": 0,
        "status": "RESOLVED",
        "regime_volatility": 18.5,
        "summary": "Baseline check: Strategy compliant. Correlated AVGO position was $1.2M and correlation was 0.72."
    }

    db.query(
        """
        CREATE (inv:Investigation {
            id: 'INV-2026-BASE-001',
            user_id: 'USR-RISK-LEAD-01',
            question: 'Routine bi-weekly risk evaluation of Quantum Momentum Alpha',
            strategy_id: 'STRAT-QUANTUM-ALPHA',
            created_at: '2026-10-01T14:00:00Z',
            status: 'COMPLETED',
            result_json: $result_json
        })
        """,
        {"result_json": json.dumps(baseline_result)}
    )

    db.query(
        """
        CREATE (dec:Decision {
            id: 'DEC-2026-BASE-001',
            action: 'MAINTAIN_CURRENT_LIMITS',
            reason: 'All risk rules satisfied. Correlated cluster exposure at $3.86M (limit $5.0M).',
            status: 'EXECUTED',
            created_at: '2026-10-01T14:30:00Z'
        })
        """
    )

    db.query("MATCH (u:User {id: 'USR-RISK-LEAD-01'}), (inv:Investigation {id: 'INV-2026-BASE-001'}) CREATE (u)-[:RAN]->(inv)")
    db.query("MATCH (inv:Investigation {id: 'INV-2026-BASE-001'}), (s:Strategy {id: 'STRAT-QUANTUM-ALPHA'}) CREATE (inv)-[:INVESTIGATED]->(s)")
    db.query("MATCH (inv:Investigation {id: 'INV-2026-BASE-001'}), (dec:Decision {id: 'DEC-2026-BASE-001'}) CREATE (inv)-[:RESULTED_IN]->(dec)")

    logger.info("FalkorDB seed completed successfully.")
    
    # Return count summary
    nodes_res = db.query("MATCH (n) RETURN count(n) AS cnt")
    edges_res = db.query("MATCH ()-[r]->() RETURN count(r) AS cnt")
    return {
        "status": "seeded",
        "nodes": nodes_res[0][0] if nodes_res else 0,
        "relationships": edges_res[0][0] if edges_res else 0,
        "primary_scenario_strategy": "STRAT-QUANTUM-ALPHA"
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    res = seed_database()
    print("Seed result:", res)
