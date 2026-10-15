# Running the project (not a production deployment)

The verified runtime is Python 3.12 on Linux. From the project root, install:

```bash
python -m pip install -r requirements-lock.txt
python -m pip check
python -m uvicorn app.main:app --port 8000
```

The API and dashboard show the frozen original ML model. The research endpoint
separately exposes the revised decision. This separation is labelled in the UI.
For new raw-data reproduction run `python scripts/rebuild.py`; never casually
rerun or tune the already-inspected stress period.

For Colab, upload notebook 00 and the complete project ZIP when setup requests it.
The notebooks contain actual local execution outputs. Their Colab upload and
optional browser proxy have not been live-tested. Python version changes in
Colab can require a different compatible environment; do not silently change
pinned scientific dependencies and report identical reproducibility.

Docker and CI definitions are supplied, but no Docker build or remote GitHub
Actions run was performed in the authoring environment. A live loopback uvicorn
server was tested, including real JSON POSTs and chunked oversize rejection.
GitHub publication remains blocked by the earlier integration write rejection.
No public site, production deployment or permanent Colab service is claimed.
