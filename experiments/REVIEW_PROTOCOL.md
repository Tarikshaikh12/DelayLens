# Fixed review experiment — protocol written before fitting

This is a new exploratory audit, not independent confirmation. Earlier development
and July–August results have already been inspected. This file and implementation
must be committed before the single experiment invocation. No tuning follows it.

## Population, information and unknown outcomes

- Predict at order approval. Feature eligibility uses approval-time fields only:
  valid order input, exactly one seller, valid purchase/approval/promise times.
  Never use final status, delivery availability, or delivery time to include or
  exclude an evaluation row. Missing/invalid approval fields are audited.
- Eventual recorded delivery after the promised calendar day is late. An absent
  or impossible delivery timestamp means UNKNOWN, not on-time. Status is not an
  input. Conflicting status/timestamp records are audited, not silently removed.
- All rankings keep unknown rows. Report confirmed late hits, selected unknowns,
  precision bounds, and random expected confirmed hits on the SAME full cohort.
  Label a metric based on known hits accordingly; it is not full-population recall.
- Development outcomes are read as of 2018-07-01, without dropping unavailable
  outcomes. This makes the development decision feasible at that date, but does
  not make unknown-outcome missingness random. Full-snapshot diagnostics are
  separate. June is excluded from selection by calendar, not by its outcomes.
- Final snapshot has no verified administrative extraction cutoff. Do not infer
  that no delivery event means a permanent failure or a cancellation date.
- Catalogue, price, promise, ZIP and geolocation values are final snapshots. Their
  presence at approval and unchanged values cannot be verified from this data.
  Claims of complete point-in-time feature provenance therefore remain qualified.

## Fixed models and history

Exactly five candidates, in tie-preference order:
1. short_promise_rule: minus promised days;
2. route_duration_rule: mean historical route duration minus promised days;
3. original_features_boosting;
4. enriched_boosting;
5. monotone_enriched_boosting.

Boosting: 180 iterations, learning rate 0.06, 15 leaves, minimum leaf 35,
L2 regularization 5, random seed 42, no early stopping. Numerical median
imputation; nominal ordinal categories with unknown codes. Numerical columns
are retained when entirely missing. No grid search or new candidates.

Enrichment: approximate ZIP-centroid great-circle distance; cumulative seller
and seller-state/customer-state route completed counts, mean duration, late
fraction, and promised days minus historical mean duration (slack). Update
history ONLY on deliveries strictly before an approval. Never update on final
status. Unknown/impossible deliveries never enter history. Shrink means/fractions
with 20 observations of global past history; before any event, use fixed
assumptions 12 days and 0.08 late. Geography is a static snapshot, not a route.

Monotone variant: non-increasing late risk in promised_days, seller_slack and
route_slack, all other coordinates held fixed. Test coordinate constraints and
jointly increasing the promise and both slack features. This is a directional
assumption, not proof of causality. No probability calibration is fitted here:
monotone calibration cannot improve queue ordering.

## Development and selection

- Fifteen calendar months, March 2017 through May 2018 inclusive.
- Each month fits on approvals in the preceding 180 days, using only valid
  deliveries strictly before the month start. Early folds can have less available
  history; report sample sizes. No outcome-based filtering of evaluation cohorts.
- Evaluate the entire feature-eligible approval-month cohort; reset capacities
  by approval date, score descending and order_id ascending for ties.
- Budgets 10, 25, 50 per day are scenarios, not justified staffing choices.
  Primary decision budget is 50; 10 and 25 are prespecified sensitivity analyses.
- Choose one best simple rule using mean per-month confirmed late hits at primary
  budget, using development only. It is one fixed rule, not a monthly oracle.
- Model selection metric: mean per-month paired difference in confirmed late hits
  against that rule. A small margin alone never establishes superiority.
- Paired bootstrap: 4,000 replicates, resampling complete approval days within
  each development month, retaining equal month weights. Seed 20261014. Compare
  all three models against BOTH rules, so selecting the best rule cannot conceal
  a weak comparison. Publish usual 95% and Bonferroni familywise intervals over
  six model/rule comparisons (two-sided alpha=0.05/6).
- Promotion requires a strictly positive known-hit difference in at least 10 of
  15 months against the best rule AND positive lower simultaneous confidence
  bounds against both rules. Additionally, the same interval must exclude zero
  using WORST-CASE unknown outcomes: candidate-only selected unknowns are on-time,
  rule-only selected unknowns are late. This is deliberately conservative.
- Among models meeting every requirement select highest mean paired difference;
  tie follows candidate order. Otherwise prefer the best development simple rule.
- Bootstrap reflects fixed fitted scores/observed days, not retraining, independent
  new regimes, or uncertainty from the unversioned source snapshot. Report that.

## June and retrospective July–August

Freeze selection BEFORE any June/stress result is read. June is a separate
censoring diagnostic; use outcomes as of July 1 AND full-snapshot coverage.
No selection uses June.

At July 1 refit the chosen model, if any, once on the previous 180 days with
available completed outcomes. Score July–August once; history can advance on
completed events, weights cannot. ALWAYS report both fixed simple rules, the
chosen method, and the supplied frozen original ML artifact as requested audit
comparators. No losing development model is newly assessed on the stress period.
The original artifact has its own older training/calibration and conditional
cohort; it is not a candidate for this new selection.

For monthly model lift diagnostics before March 2017 report NA: no preregistered
out-of-time model is available. March 2017–May 2018 uses the fixed original-feature
boosting comparator and all candidate results. June uses the same fixed
original-feature comparator solely for diagnosis. July–August uses the frozen
original artifact plus any selected model. Never label in-sample scores as
out-of-time performance. Bucket lift uses contributions to the FULL daily queue,
not separate per-bucket quotas; also publish selection counts and known labels.

Paired stress intervals (4,000 whole-day draws, no refits) cover original ML vs
both simple rules, and the selected method vs both rules at all three budgets.
Also reproduce the original delivered-only cohort comparison as a clearly marked
legacy sensitivity to audit the original 164-vs-258 claim, never for selection.

## Diagnostics and execution controls

Raw approval-month diagnostics from 2017-01 through 2018-08: counts, promised-day
buckets (<=10, 11–20, 21–30, >30, invalid), medians, observed late rates, unknown
counts, and ALL status counts/shares (including shipped/canceled/unavailable).
Do not conflate raw approval-month cohorts with feature-eligible prediction rows.

All raw files must match the pinned source manifest. Processed cache fingerprint
includes raw hashes and preparation code hashes, plus the cache file checksum.
A stale cache is rebuilt, never silently trusted. A one-command rebuild uses raw
files directly. An exclusive run ledger refuses a second experiment execution
in the same checkout; packaged reports can be verified without retraining.

Only engineering failures may be repaired; no changed model or evaluation
settings after score inspection. Any interrupted invocation and repairs must be
recorded. Run tests on synthetic data before committing and fitting. Final reports
and README tables are generated from machine-readable outputs, not hand-entered.
