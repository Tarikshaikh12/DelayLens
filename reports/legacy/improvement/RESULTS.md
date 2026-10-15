# Can a stronger approach beat the simple rule?

## What we actually tried

We ran a fixed follow-up experiment, not just a list of suggestions. We added
approximate seller–customer distance and seller/route history, tested a separate
delivery-time regression model, and selected using the actual review budget.
The protocol is in `experiments/PROTOCOL.md`; code is in `experiments/improve.py`.
No hyperparameter search was performed after viewing these results.

The original app and its fitted model are unchanged. This is an experimental
extension, not an upgraded model silently substituted into the dashboard.

## Development: January–June 2018

Every month trains on the preceding 180 days. Only labels observed before that
month's start are used for fitting. Historical features are updated only after
an earlier order is delivered, strictly before the current order is approved.
Thus, during an evaluation month, completed earlier deliveries can update
history, but model parameters stay frozen. This assumes timely outcome ingestion.

All development evaluation labels must also be available before 1 July, when
selection occurs. This removes 1, 3, 0, 4, 22 and 1,611 orders respectively.
**June is heavily affected:** only seven late deliveries remain in its eligible
evaluation cohort. This outcome-maturity filter creates selection bias; these
results must not be presented as an unbiased evaluation of all incoming orders.

| Fixed approach | Late orders found, total development |
|---|---:|
| Enriched gradient boosting | 1,060 |
| Delivery-duration regression minus promise | 1,046 |
| Gradient boosting with original features | 961 |
| Historical route-duration minus promise | 835 |
| Short-promise rule | 405 |

The same maximum of 50 reviews per approval day applies to every approach.
Enriched boosting beats the short-promise rule in five of six development months.
It wins the prespecified selection criterion and is the only follow-up candidate
scored on the July–August stress check. The original-feature comparator also uses
the new rolling training scheme; it is not the original frozen logistic model.

## Retrospective July–August stress check

| Approach | July late orders found | August late orders found | Total |
|---|---:|---:|---:|
| Enriched boosting, selected on development | 81 | 91 | 172 |
| Short-promise rule | 60 | 198 | 258 |

There are 12,304 eligible orders, 599 late deliveries and 2,772 reviews.
The enriched model has 6.20% precision and 28.71% recall. The rule has 9.31%
precision and 43.07% recall. Random review is expected to find 116.3 late orders.
The original frozen model found 164; the new model finds eight more (4.9% more),
but this numerical change is **not evidence of a statistically reliable improvement**.
The enriched model still finds 86 fewer late orders than the rule.

A paired bootstrap resampling whole approval days 2,000 times gives a 95%
percentile interval of approximately [-165, -21] for enriched-minus-rule late
orders found. This describes sampling variation for fixed scores in the observed
period; it does not account for model selection, future drift or cohort bias.

**This is not an untouched test.** July–August results were already known when
we designed this follow-up. Rolling evaluation improves the investigation, but
it does not restore independent confirmation. No production or savings claim.

## What changed in August? A post-hoc diagnostic

Across the full eligible monthly cohorts, median promised duration fell from
20 days in July to 14 in August. Orders promised within ten days increased from
739 to 2,152. Their late fraction increased from 5.82% to 13.75%.
Among late orders, median promised duration fell from 18 days to seven days.

These observed changes help explain why a short-promise rule became much more
competitive. They do **not** establish what caused the changes. The dataset is a
final historical snapshot and delivered-only cohort; extraction boundaries and
missing undelivered outcomes can also distort late-period comparisons.
See `monthly_shift.csv`. This diagnostic was added after the scores were viewed;
it did not change features, models, selection or reported scores.

## Decision

Do not replace the API model or claim the limitation is solved.
The richer model is better in some periods and still unreliable across the
observed change. A useful next project phase would evaluate promise-aware
hybrids or adaptive retraining with delayed labels on genuinely new data.
Doing another search against August would be development, not proof.

The experiment itself strengthens the portfolio: it includes an implemented
hypothesis, event-time leakage tests, a fixed selection criterion, comparison
against strong simple methods, and a clear decision based on the evidence.

## Reproduce

From the repository root, after installing the project and downloading data:

```bash
python scripts/download_data.py
PYTHONPATH=src python experiments/improve.py
python -m pytest -q
```

On Windows, install the package first with `python -m pip install -e ".[dev]"`,
then run `python experiments/improve.py` without the PYTHONPATH prefix.
Alternatively, use `notebooks/03_Improvement_Experiment.ipynb` in Colab.
The script rebuilds the processed order table from raw data when needed.
The official pinned raw download and original cleaning contract remain required.

## Verification and execution note

Four new checks pass: strict delivery-before-approval history, invariance to
future outcome changes, invariance to input row order, and exclusion of promise
and derived slack from duration regression inputs. The experiment ran locally
against the real Olist data. Colab upload and proxy were not live-tested here.
An initial run was superseded to fix development-label availability at selection
time before its results were read; only the corrected run is reported.

The complete test suite passes: **30 tests** (26 existing plus four new).
The fixed experiment was repeated with the original pinned SciPy version after
a runtime mismatch was detected; reported counts were unchanged. No model
settings were changed. Package versions and hashes are in `reproducibility.json`.
