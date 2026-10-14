"""FastAPI application entry point for AlphaTrace.
Provides RESTful APIs for graph data, risk evaluations, and investigation reports.
"""

import logging
from typing import Any, Dict, List
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.graph.connection import get_db
from app.graph import queries
from app.graph.seed import seed_database
from app.agent.router import run_investigation
from app.models import InvestigationReport, InvestigationRequest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("alphatrace")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Explainable, graph-powered trading risk investigation agent using FalkorDB.",
)

# CORS middleware for local frontend / dev servers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check() -> Dict[str, Any]:
    """Verify backend and FalkorDB connectivity."""
    db = get_db()
    db_health = db.check_health()
    return {
        "status": "healthy" if db_health.get("status") == "healthy" else "degraded",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "database": db_health,
        "synthetic_data_disclaimer": settings.SYNTHETIC_DATA_DISCLAIMER
    }


@app.get("/api/strategies")
def list_strategies() -> List[Dict[str, Any]]:
    """List all available trading strategies."""
    return queries.get_all_strategies()


@app.get("/api/strategies/{strategy_id}")
def get_strategy(strategy_id: str) -> Dict[str, Any]:
    """Get single strategy details."""
    strat = queries.get_strategy_by_id(strategy_id)
    if not strat:
        raise HTTPException(status_code=404, detail=f"Strategy '{strategy_id}' not found.")
    return strat


@app.get("/api/strategies/{strategy_id}/positions")
def get_strategy_positions(strategy_id: str) -> List[Dict[str, Any]]:
    """Get direct positions held by a strategy."""
    strat = queries.get_strategy_by_id(strategy_id)
    if not strat:
        raise HTTPException(status_code=404, detail=f"Strategy '{strategy_id}' not found.")
    return queries.get_strategy_direct_positions(strategy_id)


@app.get("/api/strategies/{strategy_id}/graph")
def get_strategy_graph_subnetwork(strategy_id: str) -> Dict[str, Any]:
    """Retrieve node-link subnetwork around a strategy for visual rendering.
    Includes Strategy, traded Assets, connected correlated Assets, peer Strategies, and Regime.
    """
    strat = queries.get_strategy_by_id(strategy_id)
    if not strat:
        raise HTTPException(status_code=404, detail=f"Strategy '{strategy_id}' not found.")

    direct_pos = queries.get_strategy_direct_positions(strategy_id)
    connected_assets = queries.get_connected_correlated_assets(strategy_id)
    regime = queries.get_strategy_market_regime(strategy_id)
    incidents = queries.get_strategy_incidents(strategy_id)

    nodes = []
    edges = []
    seen_nodes = set()

    def add_node(node_id: str, label: str, node_type: str, metadata: dict):
        if node_id not in seen_nodes:
            seen_nodes.add(node_id)
            nodes.append({
                "id": node_id,
                "label": label,
                "type": node_type,
                "metadata": metadata
            })

    # Strategy Node
    add_node(strat["id"], strat["name"], "Strategy", {
        "pnl": strat["pnl"],
        "drawdown": strat["drawdown"],
        "sharpe": strat["sharpe"]
    })

    # Traded Assets & Positions
    for p in direct_pos:
        add_node(p["asset_id"], p["symbol"], "Asset", {"asset_type": p["asset_type"]})
        edges.append({
            "source": strat["id"],
            "target": p["asset_id"],
            "relationship": "TRADES",
            "metadata": {"exposure": p["exposure"]}
        })

    # Correlated Assets & Peer Strategies
    for c in connected_assets:
        target_asset_id = f"ASSET-{c['correlated_symbol']}"
        add_node(target_asset_id, c["correlated_symbol"], "CorrelatedAsset", {
            "type": c.get("correlated_type", "Equity"),
            "exposure": c.get("exposure", 0.0)
        })
        # Correlation Edge
        edges.append({
            "source": f"ASSET-{c['direct_symbol']}",
            "target": target_asset_id,
            "relationship": "CORRELATED_WITH",
            "metadata": {"correlation": c["correlation"], "regime": c["correlation_regime"]}
        })
        # Peer Strategy
        if c.get("other_strategy_id"):
            add_node(c["other_strategy_id"], c.get("other_strategy_name", c["other_strategy_id"]), "PeerStrategy", {})
            edges.append({
                "source": c["other_strategy_id"],
                "target": target_asset_id,
                "relationship": "TRADES",
                "metadata": {"exposure": c.get("exposure", 0.0)}
            })

    # Regime Node
    if regime:
        add_node(regime["id"], regime["label"], "MarketRegime", {"volatility": regime["volatility"]})
        edges.append({
            "source": strat["id"],
            "target": regime["id"],
            "relationship": "ACTIVE_DURING",
            "metadata": {}
        })

    # Incident Nodes
    for inc in incidents:
        add_node(inc["id"], inc["id"], "Incident", {"description": inc["description"]})
        edges.append({
            "source": strat["id"],
            "target": inc["id"],
            "relationship": "EXPERIENCED",
            "metadata": {}
        })

    return {"nodes": nodes, "edges": edges}


@app.post("/api/investigate", response_model=InvestigationReport)
def investigate_strategy(request: InvestigationRequest) -> InvestigationReport:
    """Run an explainable risk investigation for the requested strategy."""
    try:
        report = run_investigation(request)
        return report
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Investigation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal investigation error: {str(e)}")


@app.get("/api/investigations")
def list_investigations(limit: int = Query(default=15, le=50)) -> List[Dict[str, Any]]:
    """List historical investigations from graph memory."""
    return queries.get_all_investigations(limit=limit)


@app.post("/api/seed")
def reseed() -> Dict[str, Any]:
    """Reseed the graph database with synthetic test scenario data."""
    try:
        res = seed_database()
        return res
    except Exception as e:
        logger.error(f"Reseed failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.API_HOST, port=settings.API_PORT, reload=settings.API_RELOAD)
