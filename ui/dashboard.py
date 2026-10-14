"""AlphaTrace: Graph-Powered, Explainable Trading Risk Investigation Agent Dashboard.
Streamlit visual application demonstrating connected graph risk discovery.
"""

import json
from datetime import datetime
import pandas as pd
import requests
import streamlit as st

# Configure Page
st.set_page_config(
    page_title="AlphaTrace | Graph Risk Investigation Agent",
    page_icon="🕸️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling
st.markdown("""
<style>
    .report-card {
        background-color: #0e1117;
        border-radius: 10px;
        padding: 20px;
        border: 1px solid #262730;
        margin-bottom: 15px;
    }
    .metric-delta-danger {
        color: #ff4b4b;
        font-weight: bold;
    }
    .metric-delta-success {
        color: #09ab3b;
        font-weight: bold;
    }
    .banner-warning {
        background: linear-gradient(90deg, rgba(255,75,75,0.15) 0%, rgba(255,165,0,0.1) 100%);
        border-left: 5px solid #ff4b4b;
        padding: 15px 20px;
        border-radius: 4px;
        margin-bottom: 20px;
    }
    .banner-success {
        background: linear-gradient(90deg, rgba(9,171,59,0.15) 0%, rgba(0,200,83,0.05) 100%);
        border-left: 5px solid #09ab3b;
        padding: 15px 20px;
        border-radius: 4px;
        margin-bottom: 20px;
    }
    .stBadge {
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

# Direct backend API base URL
API_URL = "http://localhost:8000/api"


def fetch_api(endpoint: str, method: str = "GET", json_data: dict = None):
    try:
        url = f"{API_URL}/{endpoint}"
        if method == "GET":
            resp = requests.get(url, timeout=5)
        else:
            resp = requests.post(url, json=json_data, timeout=10)
        if resp.status_code == 200:
            return resp.json(), None
        return None, f"HTTP {resp.status_code}: {resp.text}"
    except Exception as e:
        return None, str(e)


# Top Navigation / Title
st.title("🕸️ AlphaTrace: Graph-Powered Trading Risk Investigation Agent")
st.caption("FalkorDB Graph Traversal • Deterministic Risk Engine • Persistent Investigation Memory • Explainable Evidence")

# Health Banner
health_data, health_err = fetch_api("health")
if health_err:
    st.error(f"⚠️ Could not reach AlphaTrace API server: {health_err}. Please ensure `uvicorn app.main:app` is running.")
else:
    db_info = health_data.get("database", {})
    col_h1, col_h2, col_h3, col_h4 = st.columns(4)
    with col_h1:
        st.metric("Graph Engine", db_info.get("backend", "FalkorDB"), f"{db_info.get('status', 'unknown').upper()}")
    with col_h2:
        st.metric("Graph Nodes", f"{db_info.get('node_count', 0)} entities")
    with col_h3:
        st.metric("Environment", health_data.get("version", "v1.0.0"), "Development")
    with col_h4:
        st.metric("Data Mode", "SYNTHETIC", "Non-Execution")

st.markdown("---")

# Sidebar Configuration
with st.sidebar:
    st.header("🔍 Investigation Control")

    strategies_data, strat_err = fetch_api("strategies")
    if not strategies_data:
        strategies_data = [
            {"id": "STRAT-QUANTUM-ALPHA", "name": "Quantum Momentum Alpha"},
            {"id": "STRAT-SEMI-LONG", "name": "Semiconductor Long-Bias"},
            {"id": "STRAT-TECH-FACTOR", "name": "Tech Factor Neutral"},
            {"id": "STRAT-MACRO-HEDGE", "name": "Macro Hedged Diversified"}
        ]

    strat_options = {s["name"]: s["id"] for s in strategies_data}
    selected_name = st.selectbox("Select Strategy to Investigate", list(strat_options.keys()), index=0)
    selected_strat_id = strat_options[selected_name]

    preset_questions = [
        "Why is Strategy A risky and does examining connected positions reveal hidden exposure?",
        "Which connected assets and peer desks contribute to aggregate cluster risk?",
        "What changed since the previous baseline investigation?",
        "Which codified risk rules are currently breached across desks?",
        "What evidence supports the immediate risk reduction recommendation?"
    ]
    selected_question = st.selectbox("Investigation Question", preset_questions, index=0)

    compare_memory = st.checkbox("Enable Temporal Memory Comparison", value=True)

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        run_btn = st.button("🚀 Investigate", type="primary", use_container_width=True)
    with col_btn2:
        reseed_btn = st.button("🔄 Reseed DB", use_container_width=True)

    if reseed_btn:
        with st.spinner("Reseeding FalkorDB..."):
            res, err = fetch_api("seed", method="POST")
            if err:
                st.error(f"Reseed failed: {err}")
            else:
                st.success(f"Graph reset: {res.get('nodes')} nodes, {res.get('relationships')} edges!")
                st.rerun()

    st.markdown("---")
    st.info("💡 **Scenario Guide**: Strategy `Quantum Momentum Alpha` appears completely safe in isolation (4.2% drawdown, direct exposure $3.0M under $5.0M limit). AlphaTrace's graph traversal exposes a hidden $3.25M correlated semiconductor cluster exposure held by peer desks!")


# Main Investigation Execution
if "report" not in st.session_state or run_btn or selected_strat_id != st.session_state.get("active_strat_id"):
    with st.spinner("Agent traversing FalkorDB graph and calculating exposures..."):
        report_data, err = fetch_api("investigate", method="POST", json_data={
            "strategy_id": selected_strat_id,
            "question": selected_question,
            "user_id": "USR-RISK-LEAD-01",
            "compare_with_previous": compare_memory
        })
        if err:
            st.error(f"Investigation execution failed: {err}")
            st.stop()
        st.session_state.report = report_data
        st.session_state.active_strat_id = selected_strat_id

report = st.session_state.report

# Executive Contrast Banner
if report.get("hidden_risk_detected"):
    st.markdown(f"""
    <div class="banner-warning">
        <h4 style="margin:0; color:#ff4b4b;">⚠️ HIDDEN GRAPH CONTAGION IDENTIFIED</h4>
        <p style="margin:5px 0 0 0;"><strong>Isolated View:</strong> Compliant direct book (${report.get('direct_exposure_usd'):,.2f}) with low drawdown ({report.get('max_drawdown_pct'):.1f}%).<br>
        <strong>Graph Traversed View:</strong> 2-hop correlation traversal reveals <strong>${report.get('effective_correlated_exposure_usd'):,.2f}</strong> aggregate semiconductor cluster exposure breaching Rule RR-CONC-01 by <strong>${report.get('effective_correlated_exposure_usd') - 5000000:,.2f}</strong>!</p>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
    <div class="banner-success">
        <h4 style="margin:0; color:#09ab3b;">✅ STRATEGY COMPLIANT ACROSS CONNECTED GRAPH</h4>
        <p style="margin:5px 0 0 0;">Both isolated metrics and cross-desk correlated exposures are well within defined limits.</p>
    </div>
    """, unsafe_allow_html=True)

# Top Metrics Row
m1, m2, m3, m4, m5 = st.columns(5)
with m1:
    st.metric(
        "Direct Exposure",
        f"${report.get('direct_exposure_usd', 0):,.0f}",
        "Within $5.0M Book Limit"
    )
with m2:
    corr_exp = report.get('effective_correlated_exposure_usd', 0)
    delta_val = f"+${corr_exp - report.get('direct_exposure_usd', 0):,.0f} Correlated"
    st.metric(
        "Correlated Cluster Exp.",
        f"${corr_exp:,.0f}",
        delta_val,
        delta_color="inverse" if corr_exp > 5000000 else "normal"
    )
with m3:
    st.metric(
        "Cluster Ratio",
        f"{report.get('cluster_concentration_ratio', 1.0):.2f}x",
        "Over direct capital"
    )
with m4:
    st.metric(
        "Regime Volatility",
        f"{report.get('active_regime_volatility', 0):.1f}",
        "High Vol Dispersion" if report.get('active_regime_volatility', 0) > 30 else "Normal"
    )
with m5:
    breaches = report.get('breaches_count', 0)
    st.metric(
        "Active Rule Breaches",
        f"{breaches}",
        "Critical" if breaches > 0 else "Compliant",
        delta_color="inverse" if breaches > 0 else "normal"
    )

st.markdown("<br>", unsafe_allow_html=True)

# Tabbed Interface
tab1, tab2, tab3, tab4 = st.tabs([
    "📋 Executive Report & Evidence",
    "🕸️ Connected Graph Topology",
    "🧠 Agent Memory & Deltas",
    "⚡ Actionable Recommendation & Decision"
])

with tab1:
    st.subheader("Executive Findings")
    st.write(report.get("executive_summary"))

    st.markdown("### Codified Risk Rule Evaluations")
    eval_list = report.get("evaluations", [])
    if eval_list:
        df_eval = pd.DataFrame([
            {
                "Rule ID": e["rule_id"],
                "Metric": e["metric"],
                "Limit": f"{e['limit']:,.1f} {e['unit']}",
                "Actual Value": f"{e['actual_value']:,.1f} {e['unit']}",
                "Status": "🚨 BREACHED" if e["status"] == "BREACHED" else "✅ PASSED",
                "Isolated Perspective": e["isolated_perspective"],
                "Graph Perspective": e["graph_perspective"],
                "Explanation": e["explanation"]
            }
            for e in eval_list
        ])
        st.dataframe(df_eval, use_container_width=True, hide_index=True)

    st.markdown("### Traversal Evidence Trail")
    for ev in report.get("evidence_chain", []):
        with st.expander(f"📌 [{ev.get('severity')}] {ev.get('title')}", expanded=(ev.get("severity") in ["CRITICAL", "HIGH"])):
            st.markdown(f"**Description:** {ev.get('description')}")
            if ev.get("graph_path"):
                st.code(ev.get("graph_path"), language="cypher")
            st.json(ev.get("data", {}))

    st.markdown("### Identified Data Gaps")
    for gap in report.get("missing_data_gaps", []):
        st.markdown(f"- ⚠️ **Missing Information**: {gap}")

with tab2:
    st.subheader("Multi-Hop Graph Topology & Exposure Breakdown")
    st.caption("Traversing: Strategy -> Traded Asset -> Correlated Peer Assets -> Connected Positions & Desks")

    # Fetch node-link graph data
    subgraph, g_err = fetch_api(f"strategies/{selected_strat_id}/graph")
    if subgraph:
        col_g1, col_g2 = st.columns([1, 1])

        with col_g1:
            st.markdown("#### Traced Graph Relationships")
            edges_df = pd.DataFrame([
                {
                    "Source": e["source"],
                    "Relationship": f"-[:{e['relationship']}]->",
                    "Target": e["target"],
                    "Properties": json.dumps(e.get("metadata", {}))
                }
                for e in subgraph.get("edges", [])
            ])
            st.dataframe(edges_df, use_container_width=True, hide_index=True)

        with col_g2:
            st.markdown("#### Exposure Breakdown Across Books")
            conn_data = report.get("connected_assets", [])
            direct_data = fetch_api(f"strategies/{selected_strat_id}/positions")[0] or []

            chart_items = []
            for d in direct_data:
                chart_items.append({"Book / Asset": f"Direct: {d['symbol']}", "Exposure (USD)": d["exposure"], "Type": "Direct"})
            for c in conn_data:
                chart_items.append({"Book / Asset": f"Connected: {c['correlated_symbol']} ({c.get('other_strategy_name')})", "Exposure (USD)": c["exposure"], "Type": "Correlated Peer"})

            if chart_items:
                chart_df = pd.DataFrame(chart_items)
                st.bar_chart(chart_df.set_index("Book / Asset")["Exposure (USD)"])

    st.markdown("#### Connected Asset Inventory")
    conn_list = report.get("connected_assets", [])
    if conn_list:
        df_conn = pd.DataFrame([
            {
                "Direct Traded Asset": c["direct_symbol"],
                "Correlated Asset": c["correlated_symbol"],
                "Correlation": f"{c['correlation']:.2f}",
                "Correlation Regime": c["correlation_regime"],
                "Connected Desk": c.get("other_strategy_name"),
                "Desk Exposure (USD)": f"${c['exposure']:,.2f}"
            }
            for c in conn_list
        ])
        st.dataframe(df_conn, use_container_width=True, hide_index=True)

with tab3:
    st.subheader("Persistent Investigation Memory & Temporal Deltas")
    st.caption("Detects how risk escalated since the previous baseline investigation stored in FalkorDB.")

    mem = report.get("memory_comparison")
    if mem and mem.get("deltas"):
        st.info(f"**Memory Engine Insight:** {mem.get('summary')}")

        st.markdown(f"**Baseline Investigation ID:** `{mem.get('previous_investigation_id')}` | **Recorded Date:** `{mem.get('previous_timestamp')}`")

        delta_df = pd.DataFrame([
            {
                "Parameter": d["field"],
                "Previous Value": d["previous_value"],
                "Current Value": d["current_value"],
                "Change": d["change_type"],
                "Significance": d["significance"]
            }
            for d in mem.get("deltas", [])
        ])
        st.dataframe(delta_df, use_container_width=True, hide_index=True)
    else:
        st.write("No previous investigation baseline available for delta comparison.")

with tab4:
    st.subheader("Actionable Recommendation & Risk Decision")

    dec = report.get("decision_proposed")
    if dec:
        if dec.get("status") == "PENDING":
            st.error(f"🚨 **Proposed Action:** `{dec.get('action')}`")
        else:
            st.success(f"✅ **Proposed Action:** `{dec.get('action')}`")

        st.markdown(f"**Decision ID:** `{dec.get('id')}`")
        st.markdown(f"**Reasoning:** {dec.get('reason')}")
        st.markdown(f"**Status:** `{dec.get('status')}` | **Generated At:** `{dec.get('created_at')}`")

    st.markdown("---")
    st.markdown("### Precedent Incidents Experienced")
    incidents = report.get("historical_incidents", [])
    if incidents:
        for inc in incidents:
            st.markdown(f"- **{inc.get('id')}**: {inc.get('description')}")
            st.markdown(f"  *Outcome:* {inc.get('outcome')}")
    else:
        st.write("No historical risk incidents linked to this strategy.")

st.markdown("---")
st.caption("AlphaTrace Synthetic Trading Risk Investigation Agent • FalkorDB Graph Differentiator • Antigravity Submission")
