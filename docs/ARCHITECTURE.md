# AlphaTrace Architecture

AlphaTrace is designed around a multi-tier, decoupled architecture prioritizing deterministic risk calculations, zero unparameterized Cypher queries, persistent graph memory, and local-first execution.

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

## Key Architectural Principles

1. **Deterministic Risk Mathematics:**
   All risk calculations (Direct Exposure, Effective Correlated Exposure, Contagion Index, Concentration Ratios) are strictly mathematical and unit-tested with 100% deterministic reproducibility.

2. **Graph Traversal as the Differentiator:**
   The multi-hop Cypher traversal `(Strategy)-[:TRADES]->(Asset)-[:CORRELATED_WITH]->(Asset)<-[:TRADES]-(Strategy)` materially changes the risk evaluation outcome, exposing exposures that isolated strategy checks cannot discover.

3. **Cypher Injection Immunity:**
   Every database query uses parameter dictionaries (`params={...}`). No user inputs are concatenated into Cypher query strings.

4. **Persistent Investigation Memory:**
   Investigations and proposed decisions are persisted as graph nodes (`:Investigation`, `:Decision`) linked to `:User` and `:Strategy`. The Memory Delta Engine calculates temporal parameter drift across investigation sessions.

5. **Zero Required Paid Cloud APIs:**
   The entire application runs locally using Dockerized FalkorDB, FastAPI, and Streamlit.
