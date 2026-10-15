# SUPERSEDED: historical exploratory protocol

Use REVIEW_PROTOCOL.md for the current evaluation. This older file is retained for provenance only.

# Improvement experiment: fixed before execution

This is exploratory follow-up research, motivated by an already inspected
July–August 2018 test result. Nothing in this dataset is claimed to be a new,
untouched confirmation set. The original API/model and report remain unchanged.

- Development: six monthly forward evaluations, January–June 2018.
- At each month start, fit on approvals in the preceding 180 days whose delivery
  was observed strictly before that start. No random splits or early stopping.
- Evaluate eligible delivered single-seller orders in that month with outcomes
  observed before 1 July, when the winner is selected. Report excluded immature
  labels; this particularly affects June and introduces selection bias.
- Primary selection: total late orders found across development months with
  up to 50 reviews per approval day. Deterministic order-ID tie breaking.
- Fixed candidates: short-promise rule; smoothed route-duration minus promise
  heuristic; original-feature gradient boosting; enriched gradient boosting;
  enriched delivery-duration regression minus promised days.
- Identical boosting settings: 180 iterations, learning rate .06, 15 leaves,
  minimum leaf size 35, L2=5, seed 42, early stopping disabled.
- Enrichment: approximate ZIP-centroid distance, cumulative seller and state-route
  delivery durations, late fractions, completed-order counts and promise slack.
  History uses ONLY deliveries strictly before the current approval timestamp.
  A 20-observation global-prior smoothing weight is fixed in advance. With no
  completed history, defaults are 12 days and 8% late; these are assumptions,
  explicitly marked here, not measured values.
- Geography comes from a final static snapshot and is not historically versioned.
- Select once on development; run the winner once on July–August as a retrospective
  stress check. Report paired whole-day bootstrap intervals against the rule.
- No tuning after these results. A future independent dataset is needed for
  confirmation. Outcome-maturity and delivered-only cohort selection bias remain.
- Do not replace the API model: enriched serving needs historical feature storage
  and a new input contract. This experiment delivers reproducible research first.
