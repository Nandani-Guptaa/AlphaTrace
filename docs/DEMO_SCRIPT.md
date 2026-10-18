# AlphaTrace Hackathon Demo Script & Walkthrough

Follow this 3-minute demonstration script for hackathon presentations and video submissions.

## Step 1: System Overview & Live Health Check (0:00 - 0:30)
1. Open the AlphaTrace dashboard at `http://localhost:8501`.
2. Point to the top status bar:
   - FalkorDB Graph Engine: **HEALTHY** (connected to local container).
   - Graph Nodes: **30 entities**, with active indexing.
   - Non-execution synthetic disclosure clearly stated.
3. Explain the problem statement:
   *"In multi-strategy quantitative firms, strategies that look completely healthy in isolation can mask catastrophic liquidation risk because risk engines evaluate books in silos without tracing cross-desk asset correlations."*

## Step 2: Demonstrating the Strategy-in-Isolation View (0:30 - 1:00)
1. Select **"Quantum Momentum Alpha"** in the sidebar.
2. Select the question: *"Why is Strategy A risky and does examining connected positions reveal hidden exposure?"*
3. Point to the isolated performance metrics:
   - Drawdown: **4.2%** (well within the 15% limit).
   - Direct positions: **NVDA ($1.8M)** and **MSFT ($1.2M)**.
   - Total strategy capital: **$3.0M** (under $5.0M limit).
   - In a traditional portfolio report, this strategy gets a green checkmark!

## Step 3: Triggering the FalkorDB Graph Traversal (1:00 - 1:45)
1. Click **"🚀 Investigate"**.
2. AlphaTrace executes multi-hop Cypher queries across FalkorDB:
   - Notice the **Red Warning Banner**: *"HIDDEN GRAPH CONTAGION IDENTIFIED"*.
   - Point to the metrics comparison:
     - Direct Exposure: **$3.0M**.
     - Peer gross notional: **$4.9M**; deduplicated gross cluster notional: **$7.9M** (breaching `RR-CONC-01` by **$2.9M**).
     - Correlation-adjusted stress indicator: **$7.452M**; it is a sensitivity indicator, not actual exposure or predicted loss.
3. Open **Tab 1 (Executive Report & Evidence)**:
   - Review the Codified Rule Evaluations table showing `RR-DIR-01` PASSED, but `RR-CONC-01` and `RR-CONTAG-01` BREACHED.
   - Expand the evidence chain: view the exact Cypher path:
     `(:Strategy {id: 'STRAT-QUANTUM-ALPHA'})-[:TRADES]->(:Asset {symbol: 'NVDA'})-[:CORRELATED_WITH {0.92}]->(:Asset {symbol: 'AVGO'})<-[:TRADES]-(:Strategy {id: 'STRAT-SEMI-LONG'})`.

## Step 4: Visualizing Graph Topology (1:45 - 2:15)
1. Switch to **Tab 2 (Connected Graph Topology)**.
2. Show the traced relationship table and the **Exposure Breakdown Across Books** bar chart.
3. Emphasize:
   *"The graph shows peer positions linked through correlated assets. The $7.9M figure is a distinct-position gross-notional aggregation; correlation helps identify the connected cluster but is not multiplied into concentration exposure."*

## Step 5: Persistent Investigation Memory & Actionable Decision (2:15 - 3:00)
1. Switch to **Tab 3 (Agent Memory & Deltas)**:
   - Point out the delta engine comparison against baseline `INV-2026-BASE-001`.
   - Explain that AlphaTrace shows only fields present in both saved records; missing fields are insufficient evidence, not fabricated changes.
   - Copy the investigation ID, restart FastAPI, then open `GET /api/investigations/{id}` to show that the same serialized report is retrieved from FalkorDB.
2. Switch to **Tab 4 (Actionable Recommendation & Decision)**:
   - Show the proposed decision: `REDUCE_OR_HEDGE_EXPOSURE`.
   - Explain that recommendations are simulated supervisory suggestions. Any sizing requires independent review; the system does not execute trades.
   - Review historical precedent `INC-2024-TECH-SQUEEZE` which confirms that failing to hedge this exact pattern caused a -22% cascade in 2024.
