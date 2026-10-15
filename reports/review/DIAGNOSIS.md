# Monthly data diagnosis

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

Full budget/bucket lift contributions: all_bucket_performance.csv. They retain full-day queues, not new quotas within each bucket. Early model values are unavailable, not invented.
