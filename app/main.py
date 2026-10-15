"""Serve the fitted model, a browser dashboard and an OpenAPI contract."""
from contextlib import asynccontextmanager
import hashlib
import importlib.metadata
import json
import logging
import os
from pathlib import Path
import time
import threading
import joblib
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from delaylens.features import feature_frame, CATEGORICAL, NUMERIC
from delaylens.schema import BatchInput, OrderInput
from app.middleware import BodyLimitMiddleware

ROOT = Path(__file__).resolve().parents[1]
logger = logging.getLogger("delaylens")


class Predictor:
    def __init__(self, artifact_dir):
        artifact_dir = Path(artifact_dir)
        self.metadata = json.loads((artifact_dir / "metadata.json").read_text())
        path = artifact_dir / "model.joblib"
        if hashlib.sha256(path.read_bytes()).hexdigest() != self.metadata["artifact_sha256"]:
            raise ValueError("Model checksum does not match metadata; regenerate or restore both files.")
        for name in ["scikit-learn", "numpy", "scipy", "pandas", "joblib"]:
            if importlib.metadata.version(name) != self.metadata["packages"][name]:
                raise ValueError(f"{name} version mismatch. Install the pinned dependencies or retrain.")
        # Only load an artifact produced by this project. Joblib is not a safe upload format.
        self.model = joblib.load(path)
        self.lock = threading.Lock()

    def predict(self, orders):
        X = feature_frame(orders)
        with self.lock:
            probabilities = self.model.predict_proba(X)[:, 1]
        thresholds = self.metadata["risk_band_thresholds"]
        rows = []
        for i, (order, p) in enumerate(zip(orders, probabilities)):
            warnings = []
            if order.approved_at.year != 2018:
                warnings.append("This approval year is outside the 2018 evaluation period; current performance is unverified.")
            for col in CATEGORICAL:
                if X.iloc[i][col] not in self.metadata["known_categories"][col]:
                    warnings.append(f"Unseen {col}; prediction has less direct training support.")
            for col in NUMERIC:
                low, high = self.metadata["numeric_training_ranges"][col]
                if X.iloc[i][col] < low or X.iloc[i][col] > high:
                    warnings.append(f"{col} is outside the observed training range.")
            if order.total_weight_g is None or order.total_volume_cm3 is None:
                warnings.append("Missing parcel measurements are filled using training medians.")
            band = "high" if p >= thresholds["high"] else "elevated" if p >= thresholds["elevated"] else "standard"
            rows.append({"order_id": order.order_id, "delay_probability": float(p), "risk_band": band,
                         "model_version": self.metadata["model_version"], "release_status": "research_only", "warnings": warnings})
        return rows


def create_app(artifact_dir=None):
    @asynccontextmanager
    async def lifespan(app):
        app.state.predictor, app.state.load_error = None, None
        try:
            app.state.predictor = Predictor(artifact_dir or os.getenv("MODEL_DIR", str(ROOT / "artifacts")))
        except Exception as e:
            app.state.load_error = type(e).__name__
            logger.error("Model is unavailable: %s", e)
        yield

    app = FastAPI(title="DelayLens API", version="1.0.0", lifespan=lifespan,
                  description="Historical approval-time risk for single-seller orders. Conditional on eventual recorded delivery. No causal or current-market claim.")

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        # Do not echo customer input or non-JSON values into error responses.
        errors = [{k: e[k] for k in ["loc", "msg", "type"]} for e in exc.errors()]
        return JSONResponse({"detail": errors}, status_code=422)

    @app.middleware("http")
    async def request_limits(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        response.headers["X-Process-Time-Ms"] = f"{1000*(time.perf_counter()-start):.2f}"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        return response

    app.add_middleware(BodyLimitMiddleware)

    def ready():
        if app.state.predictor is None:
            raise HTTPException(503, "Model unavailable. Run training and check the server log.")
        return app.state.predictor

    @app.get("/health", tags=["Operations"])
    def health():
        return {"status": "alive"}

    @app.get("/ready", tags=["Operations"])
    def readiness():
        predictor = ready()
        return {"status": "ready", "model_version": predictor.metadata["model_version"]}

    @app.get("/model", tags=["Model"])
    def model_info():
        return ready().metadata

    @app.post("/predict", tags=["Predictions"])
    def predict(order: OrderInput):
        return ready().predict([order])[0]

    @app.post("/predict/batch", tags=["Predictions"])
    def batch(payload: BatchInput):
        rows = ready().predict(payload.orders)
        rows.sort(key=lambda x: (-x["delay_probability"], x["order_id"]))
        for i, row in enumerate(rows):
            row["rank"] = i+1
            row["selected_for_review"] = i < payload.investigation_budget
        return {"orders": rows, "selected": min(payload.investigation_budget, len(rows)),
                "budget_scope": "This submitted batch only. Caller must supply the intended daily cohort."}

    @app.get("/demo-orders", tags=["Demo"])
    def demo_orders():
        return json.loads((ROOT/"examples/demo_batch.json").read_text())

    @app.get("/evaluation", tags=["Model"])
    def evaluation():
        ready()
        path = ROOT/"reports/metrics.json"
        if not path.exists():
            raise HTTPException(404, "Evaluation report is not included in this deployment.")
        report = json.loads(path.read_text())
        if report["model_version"] != ready().metadata["model_version"]:
            raise HTTPException(409, "Report and loaded model versions do not match.")
        return report

    @app.get("/research/evaluation", tags=["Research"])
    def research_evaluation():
        base = ROOT/"reports/review"
        if not (base/"decision.json").exists():
            raise HTTPException(404, "Revised research evidence is not included.")
        import csv
        with (base/"stress_summary.csv").open() as f:
            stress_rows = list(csv.DictReader(f))
        return {"scope": "Revised full-cohort research; API artifact remains the frozen original model",
                "decision": json.loads((base/"decision.json").read_text()),
                "stress": stress_rows,
                "independent_confirmation": False, "production_ready": False}

    app.mount("/static", StaticFiles(directory=ROOT/"app/static"), name="static")

    @app.get("/", include_in_schema=False)
    def dashboard():
        return FileResponse(ROOT/"app/static/index.html")

    return app


app = create_app()
