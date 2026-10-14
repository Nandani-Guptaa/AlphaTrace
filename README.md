# AlphaTrace: Graph-Powered, Explainable Trading Risk Investigation Agent

[![FalkorDB](https://img.shields.io/badge/Graph_Database-FalkorDB-red.svg)](https://www.falkordb.com/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Frontend-Streamlit-FF4B4B.svg)](https://streamlit.io/)
[![Python](https://img.shields.io/badge/Python-3.12%20%7C%203.14-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-16%20Passed-brightgreen.svg)]()

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
4. **Effective Correlated Cluster Exposure reaches $6,220,000**, breaching codified Rule `RR-CONC-01` ($5.0M limit) by **+$1.22M (+24.4%)**.
5. Historical graph links (`[:EXPERIENCED]`) prove that an identical correlated squeeze in 2024 sparked a forced liquidation cascade, driving drawdowns to -22%.

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

### 3. Install Dependencies & Seed Database
```bash
python -m venv .venv
.\.venv\Scripts\activate  # On Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python scripts/seed_database.py
```

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

AlphaTrace includes 16 automated tests covering:
- API health and endpoints (`tests/test_health.py`, `tests/test_api.py`)
- Parameterized Cypher query validation (`tests/test_graph_queries.py`)
- Deterministic risk formulas and breach thresholds (`tests/test_risk_evaluator.py`)
- End-to-end agent investigation workflow (`tests/test_investigation.py`)
- Persistent memory delta comparator (`tests/test_memory.py`)

All 16 tests pass deterministically in under 1 second.

---

## 🔒 Security & Safe Trading Disclosures

- **All Data is Synthetic:** All portfolio valuations, tickers, and strategy names are synthetic sample data generated exclusively for demonstration.
- **No Real Trading Execution:** AlphaTrace does not execute real-money orders or connect to broker execution gateways.
- **Zero Cypher Injection:** 100% of graph queries utilize parameterized Cypher (`params={...}`). Untrusted user strings are never concatenated into queries.
