import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from app.main import create_app

ROOT = Path(__file__).resolve().parents[1]

@pytest.fixture
def order():
    return json.loads((ROOT/"examples/single_order.json").read_text())

@pytest.fixture
def client():
    with TestClient(create_app(ROOT/"artifacts")) as test_client:
        yield test_client
