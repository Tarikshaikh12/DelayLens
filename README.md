# DelayLens — ML did not pass the missing-outcome robustness gate; simple-rule performance varies by period.

An AI-assisted research prototype for approval-time delivery-delay prioritisation, using Olist historical data. The purpose is to test whether added ML complexity is justified. It is not a production deployment.


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

## Reproduce or inspect

- Start with `START_HERE.md` and `reports/review/FULL_REVIEW.md`.
- Read the fixed protocol in `experiments/REVIEW_PROTOCOL.md`.
- Python 3.12: `python scripts/rebuild.py` creates an isolated reproduction from
  verified raw files, installs `requirements-lock.txt`, freezes the protocol,
  fits once, and writes evidence. Internet is needed for missing files/packages.
- The supplied notebooks have actual outputs. `python scripts/execute_notebooks.py`
  executes their evidence/API cells without fitting candidates again.
- `python scripts/run_checks.py` records actual test counts and live HTTP checks.
- Original API demonstration: `python -m uvicorn app.main:app --port 8000`.
  It loads the supplied old artifact, not the new preferred research method.

The runtime lock was installed and checked on Python 3.12/Linux; other platforms
are not verified. Full clean-wrapper reproduction is not run again in the
authoring session because that would repeat the fixed experiment. Its underlying
installation, raw rebuild, experiment, report generation, tests and notebook
execution are verified separately and recorded.

## Evidence and limitations

`reports/review/` is authoritative. `reports/legacy/` preserves superseded evidence
and explains the old delivered-only comparisons. Current cohort counts differ
because unresolved outcomes stay in review queues. The API evidence endpoint
retains the original model's matched legacy report and is marked accordingly.

No claim of savings, causal impact, production readiness, fully observed outcomes,
independent confirmation, or universally superior ML. Original code is MIT;
Olist data-derived artifacts/reports retain the source dataset's non-commercial
license conditions. See `DATA_LICENSE.md`.

## Verification

41 tests passed; 4 notebooks contain 16 executed code cells with stored outputs. Live POST and chunked oversize checks passed. Notebook execution used IPython in-process because separate Jupyter kernel startup was blocked. See `reports/review/VERIFICATION.md`.
