# Project structure

- `src/delaylens/data.py`: feature-eligible orders, attached observed/unknown targets.
- `review_features.py`: strict event-time history and geographic approximation.
- `cache.py`: raw, preparation-code and cache content fingerprints.
- `review.py`: frozen candidates, rolling evaluation, selection gate, stress audit.
- `experiments/REVIEW_PROTOCOL.md`: committed choices made before this run.
- `scripts/render_review.py`: generated tables and narrative; never fits models.
- `scripts/run_checks.py`: real pytest evidence plus live HTTP requests.
- `scripts/execute_notebooks.py`: real Jupyter execution, with explicit IPython
  in-process mode for environments blocking Jupyter kernel networking.
- `scripts/rebuild.py`: independent isolated reproduction from raw files.
- `app/`: frozen-original-model demonstration, distinct research evidence endpoint,
  pure ASGI bounded-body middleware and static dashboard.
- `reports/review/`: authoritative evidence and run ledger.
- `reports/legacy/`: superseded historical evidence, not the current conclusion.

The original artifact is retained to audit the earlier comparison. The new
research method is not silently wired into its probability API. Serving a route
history rule or enriched model would need a reliable historical feature service,
which is outside this research prototype.
