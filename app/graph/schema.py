"""AlphaTrace Graph Schema Definition and Index Initializer.

Nodes:
- Strategy (id, name, description, pnl, drawdown, sharpe, updated_at)
- Asset (id, symbol, asset_type)
- Position (id, quantity, exposure, currency, as_of)
- RiskRule (id, metric, limit, unit, severity)
- MarketRegime (id, label, volatility, as_of)
- Incident (id, description, timestamp, outcome)
- User (id, display_name)
- Investigation (id, user_id, question, strategy_id, created_at, status, result_json)
- Decision (id, action, reason, status, created_at)

Relationships:
- (:Strategy)-[:TRADES]->(:Asset)
- (:Asset)-[:CORRELATED_WITH {coefficient, regime}]->(:Asset)
- (:Asset)-[:HAS_POSITION]->(:Position)
- (:Position)-[:SUBJECT_TO]->(:RiskRule)
- (:Strategy)-[:ACTIVE_DURING]->(:MarketRegime)
- (:Strategy)-[:EXPERIENCED]->(:Incident)
- (:User)-[:RAN]->(:Investigation)
- (:Investigation)-[:INVESTIGATED]->(:Strategy)
- (:Investigation)-[:RESULTED_IN]->(:Decision)
- (:Investigation)-[:CITED_EVIDENCE]->(:Asset | :Position | :RiskRule | :Incident)
"""

import logging
from typing import List
from app.graph.connection import get_db

logger = logging.getLogger(__name__)

INDEXED_LABELS: List[tuple[str, str]] = [
    ("Strategy", "id"),
    ("Asset", "id"),
    ("Asset", "symbol"),
    ("Position", "id"),
    ("RiskRule", "id"),
    ("MarketRegime", "id"),
    ("Incident", "id"),
    ("User", "id"),
    ("Investigation", "id"),
    ("Decision", "id"),
]


def init_schema(graph_conn=None) -> None:
    """Initialize indices on primary keys and search fields in FalkorDB."""
    db = graph_conn or get_db()
    for label, prop in INDEXED_LABELS:
        cypher = f"CREATE INDEX FOR (n:{label}) ON (n.{prop})"
        try:
            db.query(cypher)
            logger.info(f"Schema index verified for ({label}.{prop})")
        except Exception as e:
            # FalkorDB may raise if index already exists
            logger.debug(f"Index creation note for ({label}.{prop}): {e}")
