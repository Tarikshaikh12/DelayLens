# Verification record

Checked during project creation on 14 October 2026.

| Check | Observed result |
|---|---|
| Real source data | Downloaded official Olist data; a fresh pinned-v2 download matched all nine recorded CSV checksums |
| Full training | Executed the complete pipeline; four candidate models, chronological calibration, test metrics, figures and artifact produced |
| Repeat run | Reporting/plotting fixes reproduced the same statistical metrics; no test-driven parameter tuning |
| Artifact provenance | Saved model checksum and training source hash match metadata |
| Backend tests | 26 passed, covering aggregation, calendar-day labels, maturity filtering, prediction parity, validation, ranking and failure cases |
| Notebook source | All three notebooks pass format validation and Python-cell compilation |
| Notebook computation | 27 code cells executed successfully in-process with local IPython, including an actual local HTTP request and server startup |
| Dashboard behavior | DOM checks passed for initial queue, budget update, evidence page, prediction form and invalid-budget error, using responses from the fitted API |
| JavaScript and Python syntax | JavaScript syntax check and Python compilation passed |
| GitHub upload | Blocked: GitHub returned 403 `Resource not accessible by integration` for file creation; no remote project files written |

## Verification limits

The local Jupyter kernel launcher could not use the environment's network-interface mechanism, so notebook code was executed in-process with IPython instead. The notebooks are distributed without saved outputs; the generated reports preserve the results.

The Colab-specific upload and browser-proxy branches require the user's signed-in Colab session and were not exercised here. The added ZIP route was checked by code compilation and archive/path validation, not by a live Colab session.

The browser available during creation could not open the local service URL. DOM behavior was tested, but rendered desktop/mobile visual inspection is not claimed. CSS includes responsive layouts.

Docker was unavailable in this environment. The Dockerfile, local compose configuration and GitHub Actions build/readiness checks are included, but a successful container build is not claimed. GitHub Actions could not run because publication was blocked.

No public cloud deployment, load test, prospective delivery evaluation, financial benefit, or production readiness was verified.

## Follow-up experiment verification

30 tests now pass, including four event-time/regression-input checks. The fixed
rolling experiment ran on all nine hash-verified source files using pinned
model dependencies. See `improvement/RESULTS.md`. Notebook 03 code cells compile;
its underlying experiment runs locally. Its Colab upload flow was not live-tested.
