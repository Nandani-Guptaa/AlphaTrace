# AlphaTrace: Graph-Powered, Explainable Trading Risk Investigation Agent

[![FalkorDB](https://img.shields.io/badge/Graph_Database-FalkorDB-red.svg)](https://www.falkordb.com/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Frontend-Streamlit-FF4B4B.svg)](https://streamlit.io/)
[![Python](https://img.shields.io/badge/Python-3.12%20%7C%203.14-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-graph--backed-blue.svg)]()

> **Target Hackathon Tracks:**
> 1. *Primary:* **Agents That Act on Connected Data**
> 2. *Secondary:* **Agent Memory & Auditability**

---

## 🎯 Executive Summary & The Graph Differentiator

AlphaTrace is an explainable, graph-powered trading-risk investigation agent. It solves a dangerous blind spot in quantitative finance: **evaluating trading strategies in silos**.

### The Problem: The Isolated Compliance Illusion
A risk committee reviews **Quantum Momentum Alpha (`STRAT-QUANTUM-ALPHA`)** in isolation:
- Individual drawdown: **4.2%** (Limit: 15% -> **PASSED**)
- Direct positions: **NVDA ($1.8M)** and **MSFT ($1.2M)** (Under $2.5M single-asset limit -> **PASSED**)
- Strategy direct book: **$3.0M** (Under $5.0M strategy limit -> **PASSED**)

Conventional risk tools flag this strategy as healthy and compliant.

### The Solution: Multi-Hop FalkorDB Graph Discovery
AlphaTrace traverses multi-hop graph relationships:
1. `NVDA` -[:CORRELATED_WITH {coefficient: 0.92}]-> `AVGO`.
2. `AVGO` is held with **$3,500,000 exposure** by peer desk `STRAT-SEMI-LONG` (`Semiconductor Long-Bias`).
3. Under the active **"High Volatility Dispersion"** market regime, cross-desk asset correlations spike.
4. The deduplicated **Gross Cluster Notional** is **$7,900,000** ($3.0M direct + $4.9M peer), breaching `RR-CONC-01` ($5.0M) by **$2.9M**. The separately displayed **$7.452M correlation-adjusted stress indicator** is not actual exposure and is not used as the rule input.
5. Historical graph links (`[:EXPERIENCED]`) provide synthetic precedent context; they do not prove causation or predict a future loss.

---

## 🏗️ System Architecture

```
                      ┌────────────────────────────────────────┐
                      │    Streamlit Visual Dashboard (ui/)    │
                      │  - Executive Reports                   │
                      │  - Graph Subnetwork Visualizer         │
                      │  - Investigation Memory Delta View     │
                      └──────────────────┬─────────────────────┘
                                         │ HTTP REST
                                         ▼
                      ┌────────────────────────────────────────┐
                      │       FastAPI Backend API (app/)       │
                      │  - /api/health                         │
                      │  - /api/strategies, /positions, /graph │
                      │  - /api/investigate                    │
                      │  - /api/investigations                 │
                      └──────────────────┬─────────────────────┘
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 ▼                                               ▼
┌──────────────────────────────────┐            ┌──────────────────────────────────┐
│     Agent Orchestrator (app/agent)│            │      Graph Layer (app/graph)     │
│  - tools.py: Deterministic Tools │            │  - connection.py: FalkorDB Pool  │
│  - evaluator.py: Quant Engine    │◄──────────►│  - queries.py: Parameterized Cypher
│  - evidence.py: Path Provenance  │            │  - schema.py: Indices & Schema   │
│  - memory.py: Delta Comparator   │            │  - seed.py: Synthetic Generator  │
└──────────────────────────────────┘            └────────────────┬─────────────────┘
                                                                 │ Cypher over TCP:6379
                                                                 ▼
                                                ┌──────────────────────────────────┐
                                                │       FalkorDB Graph Engine      │
                                                │  - Graph Storage & Cypher Matrix │
                                                │  - Node Labels & Indices         │
                                                │  - Investigation Audit Trail     │
                                                └──────────────────────────────────┘
```

---

## ⚡ Quickstart Guide

### 1. Prerequisites
- Python 3.12+ (or compatible installed Python)
- Docker Desktop (for FalkorDB)

### 2. Start FalkorDB
```bash
docker run -d --name alphatrace-falkordb -p 6379:6379 falkordb/falkordb:latest
```

### 3. Verify dependencies and seed the synthetic database
```bash
.\.venv\Scripts\activate  # On Linux/macOS: source .venv/bin/activate
python scripts/seed_database.py
```

`seed_database.py` intentionally clears the selected FalkorDB graph before loading the reproducible synthetic scenario. Do not run it against data you need to keep. The HTTP seed route also requires `?confirm_destructive_reset=true`.

### 4. Run Automated Health Checks & Tests
```bash
python scripts/run_checks.py
```
Or execute pytest directly:
```bash
pytest -v
```

### 5. Launch Application
In Terminal 1 (Backend API):
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

In Terminal 2 (Streamlit Dashboard):
```bash
streamlit run ui/dashboard.py
```
Open your browser to `http://localhost:8501`.
FastAPI's local OpenAPI documentation is available at `http://localhost:8000/docs`.

### Custom portfolio input

Select **Custom Portfolio** in the dashboard to upload a CSV or enter rows manually. AlphaTrace stores it as a new, isolated strategy and then uses the same investigation endpoint as the demo.

Required CSV fields are `symbol`, `quantity`, and `price`; optional fields are `asset_type` and `sector`.

```csv
symbol,quantity,price,asset_type,sector
NVDA,10,180.25,Equity,Technology
TLT,-5,92.10,ETF,Fixed Income
```

`quantity` may be negative for a short position, `price` must be finite and greater than zero, and notional is `quantity × price` in assumed USD. Gross exposure sums absolute notionals; net exposure keeps the sign. Exact duplicate rows (same symbol, price, and metadata) are aggregated; conflicting duplicates are rejected so no arbitrary price is chosen. Empty files, missing symbols, zero quantities, and invalid numbers are rejected.

Uploaded portfolios do not overwrite demo nodes or other custom strategies. No correlations, peer positions, market regimes, incidents, or drawdown history are inferred from a CSV. In their absence, relevant rules are returned as `INSUFFICIENT_EVIDENCE`, not passed, and the report does not claim the portfolio is safe.

---

## 📊 Graph Data Model

| Label | Description | Key Properties |
|---|---|---|
| `Strategy` | Trading desks and algorithmic strategies | `id`, `name`, `pnl`, `drawdown`, `sharpe` |
| `Asset` | Traded instruments and ETF proxies | `id`, `symbol`, `asset_type` |
| `Position` | Position sizing and market exposure | `id`, `quantity`, `exposure`, `currency` |
| `RiskRule` | Codified institutional limits | `id`, `metric`, `limit`, `unit`, `severity` |
| `MarketRegime` | Macro volatility environment | `id`, `label`, `volatility`, `as_of` |
| `Incident` | Historical stress events & precedents | `id`, `description`, `timestamp`, `outcome` |
| `Investigation`| Persistent investigation runs | `id`, `question`, `status`, `result_json` |
| `Decision` | Actionable risk mitigation directives | `id`, `action`, `reason`, `status` |

---

## 🧪 Automated Test Suite

AlphaTrace includes graph-backed integration tests and deterministic evaluator regression tests covering:
- API health and endpoints (`tests/test_health.py`, `tests/test_api.py` including `/health` and `/api/investigations/{id}`)
- Parameterized Cypher query validation (`tests/test_graph_queries.py`)
- Deterministic risk formulas and breach thresholds (`tests/test_risk_evaluator.py`)
- End-to-end agent investigation workflow (`tests/test_investigation.py`)
- Persistent memory delta comparator (`tests/test_memory.py`)

Run the real graph-backed tests after FalkorDB is reachable:
```bash
pytest -q
```

The test suite needs FalkorDB because it exercises real traversal and persistence; see troubleshooting if Docker is unavailable.

---

## 🔒 Security & Safe Trading Disclosures

- **All Data is Synthetic:** All portfolio valuations, tickers, and strategy names are synthetic sample data generated exclusively for demonstration.
- **No Real Trading Execution:** AlphaTrace does not execute real-money orders or connect to broker execution gateways.
- **Zero Cypher Injection:** 100% of graph queries utilize parameterized Cypher (`params={...}`). Untrusted user strings are never concatenated into queries.
- **Simulated Recommendations:** Risk mitigation directives are simulated suggestions for supervisory review, not executed trades.
- **Statistical Correlation Caveat:** Asset correlations reflect historical and regime co-movement patterns, not deterministic causation or guaranteed losses.

---

## ⚠️ Known Limitations

1. **Synthetic Data Scope:** Data is generated for demonstration of cross-desk risk propagation.
2. **Model Feed Boundaries:** Real-time Level-2 order book market depth and OTC derivative options delta hedges are currently flagged as identified data gaps rather than live exchange feeds.
3. **No External Execution:** The system is an analytical decision-support and audit agent; it does not execute orders on exchange matching engines.
4. **Position ownership model:** The synthetic graph has one position per asset. Books with several strategies holding the same asset need an explicit strategy-to-position ownership relationship before attribution can be complete.
