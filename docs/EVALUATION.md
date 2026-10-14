# AlphaTrace Evaluation & Quantitative Methodology

This document details the quantitative formulas, risk rule specifications, and deterministic evaluation methodology used by AlphaTrace.

## Mathematical Exposure Definitions

### 1. Direct Exposure
$$\text{DirectExposure}(S) = \sum_{p \in \text{Positions}(S)} \text{Exposure}(p)$$

### 2. Effective Correlated Exposure (Cluster Concentration)
When Strategy $S$ trades asset $A$, and asset $A$ is correlated with peer assets $C_i$ held by other strategies $S_k$, the effective aggregate exposure is:

$$\text{EffectiveCorrelatedExposure}(S) = \text{DirectExposure}(S) + \sum_{i} \left( r(A, C_i) \times \text{Exposure}(C_i) \right)$$

where:
- $r(A, C_i)$ is the correlation coefficient under the active market regime ($0.0 \le r \le 1.0$).
- $\text{Exposure}(C_i)$ is the dollar exposure held in asset $C_i$ across the firm.

### 3. Cluster Concentration Ratio
$$\text{ClusterRatio}(S) = \frac{\text{EffectiveCorrelatedExposure}(S)}{\text{DirectExposure}(S)}$$

### 4. Cross-Strategy Contagion Correlation Index
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
| Aggregate Cluster Exposure | **Hidden ($0)** | **$6,220,000** | **CRITICAL BREACH** ($+\$1.22\text{M}$) |
| Cross-Desk Contagion Index | **Hidden (N/A)** | **0.92 (AVGO in Strat B)** | **HIGH BREACH** ($> 0.75$) |
| Active Regime Volatility | Unadjusted | 34.2 (High Volatility) | **WARNING BREACH** ($> 30.0$) |

**Conclusion:** A strategy-only risk management check misses a $3.22M unhedged cross-strategy concentration that violates firm risk limits.
