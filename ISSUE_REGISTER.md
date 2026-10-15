# Independent-review issue register

| Issue | Status | Problem | Evidence | Remaining uncertainty / resolution |
|---|---|---|---|---|
| 1 | fixed | Regime-dependent weak baseline | raw_monthly.csv, all_monthly_performance.csv, decision.json | Both rules are compared throughout; route_duration_rule is preferred using development only. Neither rule is universally best. |
| 2 | fixed | Outcome-filtered June | review.month_cohort, outcomes_asof; monthly_performance.csv | All eligible June rows stay in queues. Availability masks labels, not rows; full-snapshot outcomes are separately reported. |
| 3 | fixed | Small winning margin treated as sufficient | decision.json; development_paired_days.csv | Requires month consistency, paired simultaneous intervals and conservative missing-outcome bounds. No model passes the full gate. |
| 4 | partly fixed | Unexplained August shift | raw_monthly.csv; raw_monthly_buckets.csv; DIAGNOSIS.md | The recorded distribution shift is measured. Policy, seasonal and administrative causes cannot be identified from this snapshot. |
| 5 | fixed | Strong simple rule absent from stress test | stress_summary.csv; stress_intervals.json | Both rules were evaluated once in the stress audit; neither result changes development selection. |
| 6 | fixed | Single-March AP selection mismatched to queue goal | REVIEW_PROTOCOL.md; review.execute; development_summary.csv | Canonical selection uses mean monthly paired capacity differences. Old AP selection is preserved only as a labelled frozen-model historical comparator. |
| 7 | fixed | Calibration confused with capacity gain | test_strict_monotone_calibration_preserves_queue; WALKTHROUGH.md | No new calibration is fitted; original positive-slope sigmoid preserves ranking. No queue benefit claimed. |
| 8 | fixed | Missing paired original-ML uncertainty | stress_intervals.json; legacy_sensitivity.json | Whole-day paired intervals cover both rules and all budgets. Original delivered-only audit also reproduced. Fixed scores only; not future-regime uncertainty. |
| 9 | fixed | Stale processed cache | cache.py; cache_verification.json; test_cache_checks_code_fingerprint_and_file_content | Verifies pinned raw bytes, preparation code and cache checksum. Canonical experiment rebuilt from raw. |
| 10 | partly fixed | Delivered-only cohort and censoring | data.py; cohort_audit.json; raw_audit.json | Unknown outcomes now stay in prediction queues. Training still uses completed events; final status lacks transition times, and unrecorded outcomes cannot be recovered. |
| 11 | fixed | Unjustified review capacity | development_summary.csv; stress_summary.csv | All prescribed budgets reported with actual review shares. They remain capacity scenarios, not a business staffing recommendation. |
| 12 | fixed | Body handling, notebook outputs and count inconsistencies | app/middleware.py; verification.json; pytest.xml; notebook_execution.json | 41 tests pass; live POST and chunked oversize verified. 16 cells executed with stored outputs via IPython. Separate Jupyter kernel/Colab/browser rendering remain unverified. |
