# AlphaTrace Synthetic Data & Scenario Specifications

All market, strategy, portfolio, and financial data used in AlphaTrace is strictly **synthetic** sample data designed to demonstrate graph-powered risk discovery for hackathons.

## Demonstration Scenario: The Hidden Correlated Contagion Trap

### 1. Isolated View (Conventional Risk Report)
A risk officer evaluating **Quantum Momentum Alpha (`STRAT-QUANTUM-ALPHA`)** in isolation observes:
- **Net PnL:** +$420,000 (+14.0%)
- **Current Drawdown:** 4.2% (Comfortably under 15% limit -> **PASSED**)
- **Direct Positions:**
  - `NVDA`: $1,800,000 (Under $2.5M single-asset limit -> **PASSED**)
  - `MSFT`: $1,200,000 (Under $2.5M single-asset limit -> **PASSED**)
- **Total Direct Exposure:** $3,000,000 (Under $5.0M strategy limit -> **PASSED**)

Conventional strategy-only metrics give this strategy a complete "GREEN" health score.

### 2. Graph Traversal View (AlphaTrace Reality)
Traversing relationships in FalkorDB reveals:
- `NVDA` -[:CORRELATED_WITH {coefficient: 0.92, regime: 'High Volatility Dispersion'}]-> `AVGO`
- `AVGO` is held with **$3,500,000 exposure** by peer desk `STRAT-SEMI-LONG` (`Semiconductor Long-Bias`).
- `NVDA` also shares a 0.88 correlation with `AMD` ($1,400,000 exposure held by `STRAT-TECH-FACTOR`).
- **Effective Correlated Cluster Exposure:**
  $$\text{Effective Exposure} = \$3.0\text{M} + (0.92 \times \$3.5\text{M}) + (0.88 \times \$1.4\text{M}) = \$6.25\text{M}$$
- Codified Rule `RR-CONC-01` (Aggregate Cluster Exposure $\le \$5.0\text{M}$) is **CRITICALLY BREACHED by +$1.25M (+25.0%)**.
- Cross-Strategy Contagion Correlation Index: **0.92** (breaches limit 0.75).
- Connected Market Regime: "High Volatility Dispersion" (volatility 34.2 vs 30.0 limit).
- Historical incident link: `[:EXPERIENCED]` links `STRAT-QUANTUM-ALPHA` to `INC-2024-TECH-SQUEEZE` where an unhedged semiconductor squeeze forced liquidation and accelerated drawdowns to -22%.

### 3. Temporal Memory Baseline
The database retains baseline investigation `INV-2026-BASE-001` recorded 14 days earlier. Comparing current graph state against this baseline demonstrates the temporal evolution:
- Strategy B escalated AVGO exposure from $1.2M to $3.5M (+191%).
- Regime shifted from low volatility to high volatility (correlation 0.72 -> 0.92).
- Cluster exposure jumped from $3.86M (compliant) to $6.25M (breached).
