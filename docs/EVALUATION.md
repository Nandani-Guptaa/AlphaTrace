# AlphaTrace Evaluation & Quantitative Methodology

This document details the quantitative formulas, risk rule specifications, and deterministic evaluation methodology used by AlphaTrace.

## Mathematical Exposure Definitions

### 1. Direct gross and net notional
$$\text{DirectGross}(S) = \sum_{p \in \text{distinct Positions}(S)} |\text{Exposure}(p)|$$

$$\text{DirectNet}(S) = \sum_{p \in \text{distinct Positions}(S)} \text{Exposure}(p)$$

### 2. Gross correlated-cluster notional (concentration-rule input)
$$\text{GrossCluster}(S) = \text{DirectGross}(S) + \sum_{i \in \text{distinct peer positions}} |\text{Exposure}(C_i)|$$

Position IDs are deduplicated before aggregation, so multiple graph paths cannot inflate the result.

### 3. Correlation-adjusted stress indicator (not exposure)
$$\text{StressIndicator}(S) = \text{DirectGross}(S) + \sum_i |r(A, C_i)| \times |\text{Exposure}(C_i)|$$

This is a sensitivity indicator only. Correlation is not a portfolio weight, causal relationship, or predicted loss.

### 4. Cluster Concentration Ratio
$$\text{ClusterRatio}(S) = \frac{\text{GrossCluster}(S)}{\text{DirectGross}(S)}$$

### 5. Cross-Strategy Contagion Correlation Index
$$\text{ContagionIndex}(S) = \max_{i} \left( r(A, C_i) \right)$$

---

## Codified Risk Rule Specifications

| Rule ID | Metric Name | Threshold Limit | Unit | Severity | Evaluation Scope |
|---|---|---|---|---|---|
| `RR-DIR-01` | Max Single Asset Direct Exposure | 2,500,000.0 | USD | HIGH | Strategy Direct Holdings |
| `RR-DD-01` | Strategy Maximum Drawdown | 15.0 | Percentage (%) | CRITICAL | Strategy Direct Performance |
| `RR-CONC-01` | Aggregate Correlated Cluster Exposure | 5,000,000.0 | USD | CRITICAL | Multi-Hop Correlated Network |
| `RR-CONTAG-01` | Cross-Strategy Contagion Correlation Index | 0.75 | Ratio (0 to 1) | HIGH | Cross-Desk Statistical Correlation |
| `RR-REGIME-01` | Regime Volatility Stress Buffer | 30.0 | Volatility Index | MEDIUM | Connected Macro Regime |

---

## The Isolation vs. Connected Graph Discrepancy

Under `STRAT-QUANTUM-ALPHA`:

| Metric | Isolated View | Graph View | Status |
|---|---|---|---|
| Direct Single-Asset Max | $1,800,000 (NVDA) | $1,800,000 | **PASS** ($\le \$2.5\text{M}$) |
| Strategy Drawdown | 4.2% | 4.2% (Historical precedent: 22%) | **PASS** ($\le 15\%$) |
| Direct Book Total | $3,000,000 | $3,000,000 | **PASS** ($\le \$5.0\text{M}$) |
| Gross Cluster Notional | **Unavailable** | **$7,900,000** | **CRITICAL BREACH** ($+\$2.90\text{M}$) |
| Correlation-adjusted stress indicator | **Unavailable** | **$7,452,000** | Sensitivity indicator only; not used as exposure |
| Cross-Desk Contagion Index | **Hidden (N/A)** | **0.92 (AVGO in Strat B)** | **HIGH BREACH** ($> 0.75$) |
| Active Regime Volatility | Unadjusted | 34.2 (High Volatility) | **WARNING BREACH** ($> 30.0$) |

**Conclusion:** The strategy-only view cannot see $4.9M of peer gross notional. The graph-enabled view finds a $7.9M deduplicated gross cluster, which breaches the configured $5.0M concentration limit.
