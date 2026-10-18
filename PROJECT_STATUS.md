# AlphaTrace Project Status

**Status:** Submission candidate; live FalkorDB verification is still required in an environment that can access Docker/localhost.
**Last audited:** 2026-10-16

## Verified in this workspace

- FastAPI, Streamlit, FalkorDB query, graph seed, deterministic evaluator, evidence, and persistence modules are present and wired together.
- The investigation path reads strategies, direct positions, correlated peer positions, regimes, incidents, rules, and history through parameterized FalkorDB queries.
- Deterministic offline checks confirm the primary fixture: $3.0M direct gross + $4.9M distinct peer gross = $7.9M gross cluster notional; its separate correlation-adjusted stress indicator is $7.452M.
- Duplicate peer paths and unidentified positions are excluded from aggregation; signed gross and net metrics are calculated separately.
- Investigation retrieval now returns the full saved report, not only a `result_data` wrapper.
- The dashboard preserves its existing dark theme and now labels peer gross, gross cluster, and correlation-adjusted stress separately.

## Changes made during this audit

1. `RR-CONC-01` now evaluates deduplicated gross cluster notional, not correlation-weighted notional.
2. The correlation-weighted value is retained only as an explicitly caveated stress indicator.
3. Memory comparison no longer supplies invented defaults for missing historical fields.
4. The destructive seed API requires explicit confirmation.
5. Focused regression fixtures cover duplicate paths, missing stable IDs, and negative/net exposure.
6. Custom portfolios can be submitted through CSV or manual dashboard entry, validated, persisted as isolated strategies, and investigated through the existing graph pipeline. Missing connected-data context is explicitly reported as insufficient evidence.

## Tests actually run

- `\.venv\Scripts\python.exe -m compileall -q app tests scripts ui` — passed.
- Offline deterministic evaluator/memory fixture — passed (primary numbers, RR-CONC threshold, missing-memory behavior).
- `\.venv\Scripts\python.exe -m pytest -q` — **6 passed, 15 skipped** in 0.24s. The skipped tests are real FalkorDB integration tests; this sandbox cannot open `localhost:6379` (`WinError 10013`) and Docker’s Windows pipe was inaccessible. This is not a passing live integration result.

## Remaining verification before submission

1. Start Docker/FalkorDB on a host with local socket access, then intentionally run `python scripts/seed_database.py` only if replacing the graph is acceptable.
2. Run `pytest -q`, `python scripts/run_checks.py`, and the backend/dashboard commands in README.
3. Run `python scripts/verify_all_strategies.py` with the API live to demonstrate the primary breach and the macro-hedge no-breach case.
4. Confirm persistence by creating an investigation, restarting FastAPI, and retrieving the returned ID.

## Known model limits

- All data and recommendations are synthetic and non-executing.
- Correlation does not imply causation, loss, or a portfolio weight.
- The synthetic model assigns one position per asset; multiple strategies holding the same asset require explicit strategy-to-position ownership before production-grade attribution.
- Custom CSV uploads assume USD prices and do not provide broker integration, live prices, correlations, regimes, incidents, or performance history.
