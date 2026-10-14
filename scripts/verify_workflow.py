"""Verification script for full end-to-end user workflow:
1. Health and Swagger Docs
2. Direct database connectivity check
3. List strategies
4. Run investigation on STRAT-QUANTUM-ALPHA
5. Inspect risk report, evidence, and decision
6. Retrieve saved investigation from FalkorDB
"""

import sys
import requests
from pathlib import Path

# Add project root
root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))

from app.graph.connection import get_db

BASE_URL = "http://127.0.0.1:8000"


def verify():
    print("--- 1. API Health & Documentation ---")
    r_health = requests.get(f"{BASE_URL}/health")
    assert r_health.status_code == 200, f"Health check failed: {r_health.status_code}"
    health_data = r_health.json()
    print("API Process Status:", health_data.get("status"))
    print("Database Backend:", health_data.get("database", {}).get("backend"))
    print("Database Node Count:", health_data.get("database", {}).get("node_count"))

    r_docs = requests.get(f"{BASE_URL}/docs")
    assert r_docs.status_code == 200, f"Docs endpoint failed: {r_docs.status_code}"
    print("FastAPI OpenAPI Docs: 200 OK")

    print("\n--- 2. Direct FalkorDB Connectivity Verification ---")
    db = get_db()
    db_health = db.check_health()
    assert db_health["status"] == "healthy", f"FalkorDB unreachable: {db_health}"
    res = db.query("MATCH (s:Strategy {id: 'STRAT-QUANTUM-ALPHA'}) RETURN s.name, s.drawdown")
    print("Direct Cypher Query Result:", res)

    print("\n--- 3. Main User Journey: Investigate STRAT-QUANTUM-ALPHA ---")
    payload = {
        "strategy_id": "STRAT-QUANTUM-ALPHA",
        "question": "Why is Strategy A risky and does examining connected positions reveal hidden exposure?",
        "user_id": "CHIEF-RISK-OFFICER",
        "compare_with_previous": True
    }
    r_inv = requests.post(f"{BASE_URL}/api/investigate", json=payload)
    assert r_inv.status_code == 200, f"Investigation failed: {r_inv.text}"
    report = r_inv.json()

    print("Investigation ID:", report["id"])
    print("Strategy Name:", report["strategy_name"])
    print("Direct Exposure (USD):", f"${report['direct_exposure_usd']:,.2f}")
    print("Effective Correlated Exposure (USD):", f"${report['effective_correlated_exposure_usd']:,.2f}")
    print("Hidden Risk Detected:", report["hidden_risk_detected"])
    print("Active Rule Breaches:", report["breaches_count"])
    print("Evidence Items Count:", len(report["evidence_chain"]))
    print("Executive Summary:", report["executive_summary"])
    print("Simulated Decision:", report["decision_proposed"]["action"])
    print("Decision Reasoning:", report["decision_proposed"]["reason"])

    print("\n--- 4. Verify Investigation Persistence in FalkorDB ---")
    inv_id = report["id"]
    r_get = requests.get(f"{BASE_URL}/api/investigations/{inv_id}")
    assert r_get.status_code == 200, f"Could not retrieve investigation by ID: {r_get.text}"
    persisted = r_get.json()
    assert persisted["id"] == inv_id
    assert persisted["strategy_id"] == "STRAT-QUANTUM-ALPHA"
    print(f"Retrieved saved investigation '{inv_id}' successfully from FalkorDB via API.")

    print("\n--- 5. Verify Direct Graph Node Persistence ---")
    cypher_check = db.query("MATCH (inv:Investigation {id: $id}) RETURN inv.id, inv.status", {"id": inv_id})
    assert len(cypher_check) == 1, "Investigation node not found in FalkorDB!"
    print("FalkorDB Node Confirmed:", cypher_check)

    print("\n==========================================")
    print("ALL END-TO-END WORKFLOW CHECKS VERIFIED OK")
    print("==========================================")


if __name__ == "__main__":
    verify()
