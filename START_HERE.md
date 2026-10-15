# Start here

This version addresses the independent review. Read `reports/review/SUMMARY.md`
first, then `reports/review/FULL_REVIEW.md` and `ISSUE_REGISTER.md`.
The source data cannot resolve every outcome or prove historical feature values.
Those limits are documented, not disguised as implementation fixes.

## Inspect the supplied results

Open the notebooks in order. Their code was executed and actual outputs are
stored. In the authoring environment, Jupyter's network-interface discovery was
blocked, so the cells were executed with IPython in process. This is disclosed
in `reports/review/notebook_execution.json`. It is not a live Colab verification.

For Colab, extract the ZIP, upload `notebooks/00_Run_in_Colab.ipynb`, run setup,
and upload the complete ZIP when prompted. Use Python 3.12 for the tested lock.
The optional dashboard proxy requires your live Colab session.

## Reproduce from raw data

With Python 3.12 and git installed, run from the extracted project:

```bash
python scripts/rebuild.py
```

This creates a separate reproduction folder, copies/verifies any available raw
files (or downloads missing ones), installs the locked dependencies, commits the
fixed protocol and runs it once. It keeps the delivered evidence unchanged.
The complete wrapper was not invoked again during authoring because that would
repeat the experiment; its underlying steps were verified separately. Ordinary
Jupyter kernel execution and Colab remain environment-dependent. If Jupyter
network discovery is blocked, `python scripts/execute_notebooks.py --in-process`
executes and stores real cell outputs without a separate kernel process.

Do not repeatedly change settings to improve July–August results. That period
is a retrospective stress test, not independent confirmation.

## Run the historical API demonstration

Install `requirements-lock.txt`, then:

```bash
python -m uvicorn app.main:app --port 8000
```

The dashboard loads the original frozen ML artifact. It is explicitly a legacy
demonstration, not the preferred method from the revised experiment. The selected
research method would require a historical-feature service before deployment.

## GitHub and LinkedIn

GitHub publication is still blocked by the previously observed integration
write-permission error. This ZIP contains the completed local source and evidence.
`protocol-history.bundle` preserves local git history; the original protocol
commit can be inspected without claiming it was published or externally registered.
Share the research question, methods, measured limitations and honest conclusion.
Do not claim savings, causal impact, production readiness or a universal ML win.
