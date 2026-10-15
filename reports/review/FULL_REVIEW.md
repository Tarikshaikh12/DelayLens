# ML did not pass the missing-outcome robustness gate; simple-rule performance varies by period.

Preferred development method: **route_duration_rule**. ML promoted: **No**.
Selection was frozen before June/July/August diagnostics. Both simple rules are
reported; July–August never chooses the preferred method.

## Development totals, confirmed late orders found

| Method | Hits @10 | Hits @25 | Hits @50 |
|---|---|---|---|
| enriched_boosting | 474 | 1085 | 1939 |
| monotone_enriched_boosting | 507 | 1110 | 1970 |
| original_features_boosting | 388 | 932 | 1748 |
| route_duration_rule | 408 | 893 | 1620 |
| short_promise_rule | 229 | 473 | 1003 |

## Paired selection evidence against route_duration_rule

| Model | Mean monthly gain | Months won | 95% paired CI | Worst-case simultaneous CI |
|---|---|---|---|---|
| original_features_boosting | 8.53 | 9 | [3.00, 14.47] | [-15.02, 0.36] |
| enriched_boosting | 21.27 | 11 | [15.33, 27.33] | [-3.36, 12.87] |
| monotone_enriched_boosting | 23.33 | 11 | [17.33, 29.40] | [-1.40, 15.22] |

These are mean monthly differences at the primary review budget. The ordinary
intervals describe fixed-score observed-label variation. The final column also
allows unobserved outcomes to favour the rule, with a simultaneous adjustment
for the prespecified model/rule comparisons. It is not a prediction interval for
new months. Passing the ordinary observed-label gate alone does not establish
robustness to missing outcomes.

## Retrospective stress results

| Method | Budget | Reviewed | Review share | Confirmed late hits | Selected unknown | Known-hit lift |
|---|---|---|---|---|---|---|
| short_promise_rule | 10 | 569 | 4.53% | 80 | 32 | 3.40 |
| short_promise_rule | 25 | 1397 | 11.13% | 141 | 49 | 2.46 |
| short_promise_rule | 50 | 2772 | 22.08% | 250 | 87 | 2.20 |
| route_duration_rule | 10 | 569 | 4.53% | 60 | 32 | 2.55 |
| route_duration_rule | 25 | 1397 | 11.13% | 139 | 49 | 2.42 |
| route_duration_rule | 50 | 2772 | 22.08% | 241 | 88 | 2.12 |
| frozen_original_ml | 10 | 569 | 4.53% | 53 | 21 | 2.25 |
| frozen_original_ml | 25 | 1397 | 11.13% | 93 | 45 | 1.62 |
| frozen_original_ml | 50 | 2772 | 22.08% | 161 | 80 | 1.41 |

Unknown outcomes stay in every queue. Known-hit lift compares confirmed late hits
to random review over exactly the same full cohort; it is not full-population
recall. Budgets are hypothetical capacities, not a staffing recommendation.
The frozen API artifact is a historical comparator, not the new selected method.

## August shift: supported observations and unresolved causes

In raw approved orders, median promised days changed from 19
in July to 14 in August. The share promised within ten
days changed from 12.60% to 33.70%;
the observed late rate in that bucket changed from 5.75%
to 13.72%. Unknown-outcome shares were
2.51% and 1.87%.

Supported: the recorded promise distribution and observed relationship with
lateness changed. The August unknown share does not show a simple increase in
missing outcomes relative to July. This alone does not exclude dataset-end
selection or timestamp errors. Unverified hypotheses: a promise-policy change,
seasonality, operational disruption, and administrative extraction effects.
The source has no policy log, status transition times or verified observation
cutoff. Do not call any one hypothesis the proven cause.

Raw diagnostic cohorts include all orders with a recorded approval in each
month. Model cohorts additionally require valid approval-time inputs and one
seller. Their counts can differ. Bucket rates use observed outcomes; exact
unknown counts and lower/upper late-rate bounds are in raw_monthly_buckets.csv.

## Raw monthly counts and status mix

| Month | Orders | Median promise | Unknown | Delivered | Shipped | Canceled | Unavailable | Other |
|---|---|---|---|---|---|---|---|---|
| 2017-01 | 760 | 39.00 | 45 | 715 | 16 | 2 | 8 | 19 |
| 2017-02 | 1765 | 31.00 | 127 | 1638 | 21 | 15 | 47 | 44 |
| 2017-03 | 2689 | 23.00 | 136 | 2554 | 45 | 31 | 32 | 27 |
| 2017-04 | 2374 | 26.00 | 96 | 2278 | 49 | 13 | 9 | 25 |
| 2017-05 | 3693 | 24.00 | 146 | 3548 | 54 | 19 | 32 | 40 |
| 2017-06 | 3252 | 24.00 | 109 | 3143 | 48 | 14 | 24 | 23 |
| 2017-07 | 3974 | 23.00 | 147 | 3828 | 54 | 23 | 52 | 17 |
| 2017-08 | 4348 | 23.00 | 131 | 4217 | 41 | 21 | 31 | 38 |
| 2017-09 | 4301 | 22.00 | 139 | 4170 | 40 | 16 | 37 | 38 |
| 2017-10 | 4590 | 23.00 | 149 | 4441 | 33 | 21 | 57 | 38 |
| 2017-11 | 7395 | 22.00 | 246 | 7150 | 71 | 29 | 86 | 59 |
| 2017-12 | 5832 | 27.00 | 157 | 5675 | 58 | 7 | 43 | 49 |
| 2018-01 | 7187 | 26.00 | 196 | 6991 | 73 | 32 | 47 | 44 |
| 2018-02 | 6706 | 24.00 | 171 | 6536 | 56 | 71 | 31 | 12 |
| 2018-03 | 7288 | 22.00 | 205 | 7083 | 134 | 23 | 16 | 32 |
| 2018-04 | 6778 | 23.00 | 154 | 6639 | 99 | 14 | 6 | 20 |
| 2018-05 | 7066 | 22.00 | 126 | 6940 | 54 | 24 | 16 | 32 |
| 2018-06 | 6164 | 28.00 | 70 | 6097 | 42 | 18 | 4 | 3 |
| 2018-07 | 6176 | 19.00 | 155 | 6050 | 62 | 39 | 12 | 13 |
| 2018-08 | 6620 | 14.00 | 124 | 6504 | 47 | 32 | 13 | 24 |

## Promised-day buckets: share / observed late rate

| Month | <=10 share / observed late | 11-20 share / observed late | 21-30 share / observed late | >30 share / observed late | Invalid share |
|---|---|---|---|---|---|
| 2017-01 | 0.00% / NA | 0.13% / 0.00% | 15.92% / 5.13% | 83.95% / 2.51% | 0.00% |
| 2017-02 | 0.00% / NA | 0.62% / 27.27% | 48.67% / 3.25% | 50.71% / 2.06% | 0.00% |
| 2017-03 | 0.00% / NA | 24.06% / 3.39% | 56.45% / 3.73% | 19.49% / 8.88% | 0.00% |
| 2017-04 | 0.00% / NA | 10.95% / 11.51% | 59.31% / 5.83% | 29.65% / 6.12% | 0.08% |
| 2017-05 | 2.98% / 14.15% | 23.86% / 4.58% | 53.48% / 1.95% | 19.69% / 2.45% | 0.00% |
| 2017-06 | 0.77% / 8.00% | 23.62% / 3.64% | 58.12% / 2.73% | 17.50% / 2.94% | 0.00% |
| 2017-07 | 1.11% / 7.50% | 29.74% / 1.93% | 53.65% / 2.38% | 15.50% / 5.62% | 0.00% |
| 2017-08 | 1.03% / 6.82% | 30.52% / 2.96% | 52.69% / 2.78% | 15.75% / 2.73% | 0.00% |
| 2017-09 | 3.07% / 10.00% | 35.97% / 4.48% | 50.36% / 4.17% | 10.60% / 3.66% | 0.00% |
| 2017-10 | 2.72% / 6.90% | 33.33% / 4.59% | 49.67% / 4.30% | 14.27% / 2.05% | 0.00% |
| 2017-11 | 1.18% / 10.98% | 36.32% / 10.27% | 53.10% / 14.01% | 9.40% / 9.84% | 0.00% |
| 2017-12 | 0.07% / 33.33% | 17.11% / 4.43% | 51.13% / 8.93% | 31.69% / 7.94% | 0.00% |
| 2018-01 | 0.03% / 50.00% | 19.34% / 3.24% | 56.55% / 6.59% | 24.09% / 5.43% | 0.00% |
| 2018-02 | 0.37% / 24.00% | 26.35% / 11.01% | 55.74% / 16.42% | 17.52% / 8.49% | 0.01% |
| 2018-03 | 3.40% / 8.71% | 40.61% / 16.29% | 42.43% / 23.92% | 13.56% / 15.82% | 0.00% |
| 2018-04 | 3.16% / 2.44% | 30.69% / 4.29% | 49.84% / 4.67% | 16.32% / 5.48% | 0.00% |
| 2018-05 | 7.56% / 6.15% | 36.73% / 8.93% | 36.87% / 6.44% | 18.85% / 2.28% | 0.00% |
| 2018-06 | 3.55% / 3.70% | 18.79% / 0.79% | 39.07% / 1.51% | 38.60% / 0.76% | 0.00% |
| 2018-07 | 12.60% / 5.75% | 43.07% / 2.86% | 34.97% / 3.36% | 9.36% / 0.88% | 0.00% |
| 2018-08 | 33.70% / 13.72% | 42.55% / 3.49% | 17.07% / 1.15% | 6.59% / 0.00% | 0.09% |

## Monthly rule/model known-hit lift at primary budget

| Month | Short-rule lift | Route-rule lift | Model lift | Model |
|---|---|---|---|---|
| 2017-01 | 1.13 | 1.13 | NA | not available |
| 2017-02 | 1.05 | 1.05 | NA | not available |
| 2017-03 | 0.73 | 0.82 | 0.86 | original_features_boosting |
| 2017-04 | 1.06 | 1.09 | 1.03 | original_features_boosting |
| 2017-05 | 1.49 | 1.52 | 1.18 | original_features_boosting |
| 2017-06 | 1.14 | 1.14 | 1.27 | original_features_boosting |
| 2017-07 | 0.78 | 1.05 | 0.97 | original_features_boosting |
| 2017-08 | 0.95 | 1.07 | 1.19 | original_features_boosting |
| 2017-09 | 0.80 | 1.43 | 1.13 | original_features_boosting |
| 2017-10 | 1.14 | 1.60 | 1.43 | original_features_boosting |
| 2017-11 | 0.69 | 1.17 | 1.49 | original_features_boosting |
| 2017-12 | 0.60 | 0.98 | 1.16 | original_features_boosting |
| 2018-01 | 0.71 | 1.05 | 1.44 | original_features_boosting |
| 2018-02 | 0.52 | 1.22 | 1.28 | original_features_boosting |
| 2018-03 | 0.45 | 0.92 | 0.96 | original_features_boosting |
| 2018-04 | 0.51 | 1.65 | 1.60 | original_features_boosting |
| 2018-05 | 0.83 | 1.44 | 2.04 | original_features_boosting |
| 2018-06 | 1.02 | 1.98 | 2.46 | original_features_boosting |
| 2018-07 | 1.21 | 1.54 | 1.64 | frozen_original_ml |
| 2018-08 | 2.87 | 2.52 | 1.26 | frozen_original_ml |

## Development monthly confirmed late hits at primary budget

| month | enriched_boosting | monotone_enriched_boosting | original_features_boosting | route_duration_rule | short_promise_rule |
|---|---|---|---|---|---|
| 2017-03 | 53 | 72 | 57 | 54 | 48 |
| 2017-04 | 103 | 96 | 94 | 99 | 96 |
| 2017-05 | 56 | 57 | 53 | 68 | 67 |
| 2017-06 | 53 | 54 | 58 | 52 | 52 |
| 2017-07 | 48 | 46 | 41 | 44 | 33 |
| 2017-08 | 50 | 57 | 50 | 45 | 40 |
| 2017-09 | 94 | 91 | 68 | 86 | 48 |
| 2017-10 | 88 | 90 | 88 | 98 | 70 |
| 2017-11 | 229 | 228 | 209 | 163 | 97 |
| 2017-12 | 179 | 185 | 123 | 104 | 64 |
| 2018-01 | 156 | 159 | 117 | 85 | 58 |
| 2018-02 | 179 | 190 | 236 | 226 | 96 |
| 2018-03 | 315 | 305 | 277 | 267 | 130 |
| 2018-04 | 145 | 144 | 103 | 106 | 33 |
| 2018-05 | 191 | 196 | 174 | 123 | 71 |

## Stress results by month and budget

| month | method | budget | confirmed_late_found | selected_unknown | lift_known_hits |
|---|---|---|---|---|---|
| 2018-07 | short_promise_rule | 10 | 22 | 17 | 2.19 |
| 2018-08 | short_promise_rule | 10 | 58 | 15 | 4.29 |
| 2018-07 | short_promise_rule | 25 | 30 | 28 | 1.27 |
| 2018-08 | short_promise_rule | 25 | 111 | 21 | 3.29 |
| 2018-07 | short_promise_rule | 50 | 56 | 52 | 1.21 |
| 2018-08 | short_promise_rule | 50 | 194 | 35 | 2.87 |
| 2018-07 | route_duration_rule | 10 | 22 | 17 | 2.19 |
| 2018-08 | route_duration_rule | 10 | 38 | 15 | 2.81 |
| 2018-07 | route_duration_rule | 25 | 45 | 23 | 1.91 |
| 2018-08 | route_duration_rule | 25 | 94 | 26 | 2.78 |
| 2018-07 | route_duration_rule | 50 | 71 | 46 | 1.54 |
| 2018-08 | route_duration_rule | 50 | 170 | 42 | 2.52 |
| 2018-07 | frozen_original_ml | 10 | 27 | 10 | 2.69 |
| 2018-08 | frozen_original_ml | 10 | 26 | 11 | 1.92 |
| 2018-07 | frozen_original_ml | 25 | 47 | 23 | 1.99 |
| 2018-08 | frozen_original_ml | 25 | 46 | 22 | 1.36 |
| 2018-07 | frozen_original_ml | 50 | 76 | 41 | 1.64 |
| 2018-08 | frozen_original_ml | 50 | 85 | 39 | 1.26 |

## What the data cannot establish

- Missing deliveries are unresolved/unknown, not automatically on-time or late.
  Canceled and unavailable orders have competing outcomes that this delivery
  target cannot resolve. Training still learns from completed deliveries only.
- Final-snapshot price, product, ZIP, geolocation and promise values are assumed
  to have been available unchanged at approval; the dataset cannot prove it.
- All data has been inspected in earlier work. A committed local protocol protects
  this run against changing choices, but is not independent external preregistration.
- Calibration is not fitted in this audit. The original positive-slope sigmoid is
  strictly monotone and cannot improve its queue ranking. It did not make the
  old model's capacity performance better.
- Daily queues are retrospective next-shift prioritisation, not instant online
  action at approval. No intervention was tested. No causal impact or savings.
- Bootstrap intervals hold scores and fitted models fixed. They do not cover new
  regimes, future label completeness or repeated investigation of this dataset.

## Protocol and run provenance

Commit: `f747128b5c03de6a648e0e32317880b6182cd4a9`. Full hashes, start/end times and package versions: `RUN_LEDGER.json`. The experiment was invoked once and completed; no candidate settings were changed after its results.

## Issue register

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

## Paired retrospective uncertainty

| Candidate | Rule | Budget | Difference | Paired 95% CI | Active days |
|---|---|---|---|---|---|
| frozen_original_ml | short_promise_rule | 10 | -27.00 | [-53.00, -1.00] | 58 |
| frozen_original_ml | short_promise_rule | 25 | -48.00 | [-98.00, -5.00] | 58 |
| frozen_original_ml | short_promise_rule | 50 | -89.00 | [-176.00, -21.00] | 58 |
| frozen_original_ml | route_duration_rule | 10 | -7.00 | [-22.00, 8.00] | 58 |
| frozen_original_ml | route_duration_rule | 25 | -46.00 | [-75.00, -18.00] | 58 |
| frozen_original_ml | route_duration_rule | 50 | -80.00 | [-145.00, -27.00] | 58 |
| route_duration_rule | short_promise_rule | 10 | -20.00 | [-39.00, -2.00] | 58 |
| route_duration_rule | short_promise_rule | 25 | -2.00 | [-32.00, 26.03] | 58 |
| route_duration_rule | short_promise_rule | 50 | -9.00 | [-40.00, 18.00] | 58 |

# Actual verification

- Pytest: 41 passed, 0 failed, 0 errors, 0 skipped. Source: pytest.xml and verification.json.
- Live uvicorn JSON POST preservation: True.
- Live chunked oversized POST rejected: True.
- Executed notebooks: 4; executed code cells: 16; error outputs: 0.
- Fresh dependency installation and compatibility check succeeded; locked reinstall dry-run required no changes. Installation evidence: environment.json.
- Dashboard DOM behaviour check passed using actual API responses. No visual browser rendering claim.
- Notebook syntax/format checks passed. Real cells executed with IPython in-process.
- Ordinary Jupyter kernel attempt failed due environment network-interface discovery denial. That failure was not presented as a successful Jupyter/Colab session.
- One experiment invocation completed under protocol commit `f747128b5c03de6a648e0e32317880b6182cd4a9`. No tuning or experimental re-runs followed its scores.

## Not run or not verifiable

- The full fresh-checkout rebuild wrapper was not invoked a second time; doing so would repeat the experiment. Its component installation, raw rebuild, fit, reporting, tests and notebook execution ran separately.
- Docker build/runtime and remote GitHub Actions were not run here. GitHub upload remains blocked by the previously observed integration permission error.
- Windows/macOS dependency compatibility, live Colab upload/proxy and rendered browser appearance were not verified.
- Exact extraction cutoff, outcome collection completeness, status transition dates, historical field revisions and the causal reason for August's shift are unavailable.
- Out-of-time model lift before the preregistered development start is unavailable, explicitly marked NA. Both simple rules have descriptive early-month results.
- No new independent cohort, deployment, intervention experiment, savings estimate or production readiness validation.
