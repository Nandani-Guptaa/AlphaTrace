"""Verify all 4 strategies return consistent, well-formed investigation reports."""
import requests

API = "http://localhost:8000/api"
STRATEGIES = [
    "STRAT-QUANTUM-ALPHA",
    "STRAT-SEMI-LONG",
    "STRAT-TECH-FACTOR",
    "STRAT-MACRO-HEDGE",
]

REQUIRED_FIELDS = [
    "investigation_id", "strategy_id", "executive_summary",
    "direct_exposure_usd", "effective_correlated_exposure_usd",
    "cluster_concentration_ratio", "hidden_risk_detected", "breaches_count",
    "evaluations", "evidence_chain", "connected_assets",
    "decision_proposed", "historical_incidents",
]

def main():
    print("=== AlphaTrace Strategy Verification ===\n")
    all_ok = True
    for strat_id in STRATEGIES:
        payload = {"strategy_id": strat_id, "question": "E2E verify", "user_id": "USR-TEST", "compare_with_previous": False}
        try:
            r = requests.post(f"{API}/investigate", json=payload, timeout=15)
            if r.status_code != 200:
                print(f"[FAIL] {strat_id}: HTTP {r.status_code} - {r.text[:200]}")
                all_ok = False
                continue
            d = r.json()
            missing = [f for f in REQUIRED_FIELDS if f not in d]
            if missing:
                print(f"[WARN] {strat_id}: Missing fields: {missing}")
                all_ok = False
            de = d.get("direct_exposure_usd", 0)
            ce = d.get("effective_correlated_exposure_usd", 0)
            cr = d.get("cluster_concentration_ratio", 0)
            breaches = d.get("breaches_count", 0)
            hidden = d.get("hidden_risk_detected", False)
            n_conn = len(d.get("connected_assets", []))
            n_ev = len(d.get("evidence_chain", []))
            n_evals = len(d.get("evaluations", []))
            # Sanity checks
            assert ce >= de, f"Correlated exposure {ce} < direct {de}"
            assert cr >= 1.0, f"Cluster ratio {cr} < 1.0"
            assert n_evals > 0, "No rule evaluations"
            assert n_ev > 0, "No evidence chain items"
            dec = d.get("decision_proposed")
            assert dec is not None, "No decision proposed"
            print(f"[OK ] {strat_id}")
            print(f"       Direct Notional Exposure :  ${de:>12,.2f}")
            print(f"       Correlated Cluster Exp.  :  ${ce:>12,.2f}  (ratio {cr:.2f}x)")
            print(f"       Hidden Risk Detected     :  {hidden}")
            print(f"       Rule Breaches            :  {breaches}")
            print(f"       Connected Assets         :  {n_conn}")
            print(f"       Evidence Items           :  {n_ev}")
            print(f"       Decision Action          :  {dec.get('action')}")
            print()
        except AssertionError as ae:
            print(f"[FAIL] {strat_id}: Assertion error - {ae}")
            all_ok = False
        except Exception as ex:
            print(f"[FAIL] {strat_id}: Exception - {ex}")
            all_ok = False

    print("=== Investigation History ===")
    r2 = requests.get(f"{API}/investigations?limit=5", timeout=10)
    if r2.status_code == 200:
        invs = r2.json()
        print(f"Stored investigations (last 5): {len(invs)}")
        for inv in invs[:3]:
            print(f"  {inv.get('investigation_id')} | {inv.get('strategy_id')} | {inv.get('timestamp','?')}")
    else:
        print(f"Could not fetch investigations: HTTP {r2.status_code}")

    print()
    print("=== Node / Edge Count ===")
    rh = requests.get(f"{API}/health", timeout=5)
    if rh.status_code == 200:
        db = rh.json().get("database", {})
        print(f"FalkorDB node count: {db.get('node_count')}")

    print()
    print("=== RESULT:", "ALL PASS" if all_ok else "SOME FAILURES ===")

if __name__ == "__main__":
    main()
