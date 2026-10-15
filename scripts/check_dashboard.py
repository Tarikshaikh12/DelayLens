"""Test dashboard DOM behavior using responses from the actual fitted API.

Run `npm ci` first. This does not render screenshots or emulate Colab's proxy.
"""
import json
import subprocess
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.main import create_app

with TestClient(create_app()) as client:
    fixture = {path: client.get(path).json() for path in ["/model", "/evaluation", "/demo-orders"]}
    fixture["/predict/batch"] = client.post("/predict/batch", json=fixture["/demo-orders"]).json()
    fixture["/predict"] = client.post("/predict", json=fixture["/demo-orders"]["orders"][0]).json()
with tempfile.TemporaryDirectory() as temp:
    path = Path(temp)/"responses.json"
    path.write_text(json.dumps(fixture))
    subprocess.run(["node", str(ROOT/"scripts/check_dashboard.cjs"), str(path)], cwd=ROOT, check=True)
