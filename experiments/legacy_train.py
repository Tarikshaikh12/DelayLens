# ARCHIVED, SUPERSEDED IMPLEMENTATION: do not use for new evaluation.
# Preserved solely to audit historical results; canonical entry is delaylens.review.
"""Run once from raw tables through the frozen July/August holdout report.

Usage: python -m delaylens.train --data-dir data/raw --output-dir .
"""
import argparse
import hashlib
import importlib.metadata
import json
import platform
import time
from datetime import datetime, timezone
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler
from sklearn.metrics import precision_recall_curve
from sklearn.calibration import calibration_curve
from threadpoolctl import threadpool_limits
from .data import build_dataset, temporal_split
from .features import FEATURES, NUMERIC, CATEGORICAL
from .model import CalibratedRiskModel
from .evaluation import metrics, capacity_metrics, day_bootstrap


def write_json(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2, allow_nan=False) + "\n")


def candidate_models():
    numeric = Pipeline([("impute", SimpleImputer(strategy="median", add_indicator=True)), ("scale", StandardScaler())])
    onehot = ColumnTransformer([("numeric", numeric, NUMERIC), ("category", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL)])
    # HGB can treat category codes as nominal (not an arbitrary numeric ordering).
    ordinal = ColumnTransformer([("numeric", SimpleImputer(strategy="median"), NUMERIC),
                                 ("category", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1), CATEGORICAL)])
    return {
        "constant_prior": Pipeline([("preprocess", clone(onehot)), ("model", DummyClassifier(strategy="prior"))]),
        "logistic_regression": Pipeline([("preprocess", clone(onehot)), ("model", LogisticRegression(C=0.2, max_iter=1500, random_state=42))]),
        "random_forest": Pipeline([("preprocess", clone(onehot)), ("model", RandomForestClassifier(n_estimators=180, max_depth=14, min_samples_leaf=12, n_jobs=2, random_state=42))]),
        "hist_gradient_boosting": Pipeline([("preprocess", ordinal), ("model", HistGradientBoostingClassifier(max_iter=180, learning_rate=0.06, max_leaf_nodes=15, min_samples_leaf=35, l2_regularization=5, early_stopping=False, categorical_features=[False]*len(NUMERIC)+[True]*len(CATEGORICAL), random_state=42))]),
    }


def make_figures(output, test, model_p, raw_p, baseline_p, budget_rows, importance):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "DejaVu Sans", "axes.spines.top": False, "axes.spines.right": False,
                         "axes.titleweight": "bold", "figure.facecolor": "#f6f8fa", "axes.facecolor": "#f6f8fa"})
    fig, axs = plt.subplots(1, 2, figsize=(12, 4.6), layout="constrained")
    pr, re, _ = precision_recall_curve(test.late, model_p)
    axs[0].step(re, pr, where="post", color="#087f74", label="DelayLens", linewidth=2)
    # A straight line from the no-predictions endpoint would misleadingly inflate
    # the constant classifier's apparent PR area. Show its AP reference instead.
    axs[0].axhline(test.late.mean(), color="#e8a735", linestyle="--", label="Constant-score AP / late rate")
    axs[0].set(xlabel="Recall", ylabel="Precision", title="Can we rank late orders higher?", xlim=(0,1), ylim=(0,1))
    axs[0].legend()
    for name, p, color in [("Before calibration", raw_p, "#7b8794"), ("After calibration", model_p, "#087f74")]:
        frac, pred = calibration_curve(test.late, p, n_bins=8, strategy="quantile")
        axs[1].plot(pred, frac, "o-", label=name, color=color)
    axs[1].plot([0,1], [0,1], "--", color="#c4ccd2", label="Perfect calibration")
    limit = min(1, max(.3, float(np.quantile(raw_p, .98))))
    axs[1].set(xlabel="Mean predicted probability", ylabel="Observed late fraction", title="Do the probabilities match reality?", xlim=(0,limit), ylim=(0,limit))
    axs[1].legend()
    fig.savefig(output/"figures/model_quality.png", dpi=170); plt.close(fig)
    fig, ax = plt.subplots(figsize=(8,4), layout="constrained")
    for method, color in [("model", "#087f74"), ("short_promise_rule", "#3f5d8d"), ("random", "#b7bec5")]:
        rows = [r for r in budget_rows if r["method"] == method]
        ax.plot([r["budget_per_day"] for r in rows], [100*r["precision"] for r in rows], "o-", label=method.replace("_", " "), color=color)
    ax.set(xlabel="Daily investigation capacity", ylabel="Late orders among selected (%)", title="Which queue uses the team's capacity better?")
    ax.legend(); fig.savefig(output/"figures/capacity.png", dpi=170); plt.close(fig)
    fig, ax = plt.subplots(figsize=(8,4.8), layout="constrained")
    top = importance.sort_values("mean_ap_drop").tail(10)
    ax.barh(top.feature, top.mean_ap_drop, color="#087f74")
    ax.set(xlabel="Drop in validation average precision after shuffling", title="Useful inputs in the selection model")
    fig.savefig(output/"figures/feature_importance.png", dpi=170); plt.close(fig)


def run(data_dir, output_dir):
    started = time.perf_counter()
    root = Path(output_dir)
    reports, artifacts = root/"reports", root/"artifacts"
    for d in [reports/"figures", artifacts, root/"data/processed"]: d.mkdir(parents=True, exist_ok=True)
    df, requests, audit = build_dataset(Path(data_dir))
    parts, split_report = temporal_split(df)
    write_json(reports/"data_audit.json", audit)
    write_json(reports/"split_summary.json", split_report)
    df.to_csv(root/"data/processed/orders.csv", index=False)
    train, val, cal, test = [parts[n] for n in ["train", "validation", "calibration", "test"]]
    models, validation, fitted = candidate_models(), {}, {}
    for name, estimator in models.items():
        print(f"Training {name} on {len(train):,} orders...", flush=True)
        t = time.perf_counter()
        estimator.fit(train[FEATURES], train.late)
        p = estimator.predict_proba(val[FEATURES])[:, 1]
        validation[name] = metrics(val, p)
        validation[name]["fit_seconds"] = time.perf_counter() - t
        fitted[name] = estimator
        print(f"  Validation average precision: {validation[name]['average_precision']:.4f}", flush=True)
    # Selection happens BEFORE seeing test scores. Fewer models is deliberate.
    selected = max(validation, key=lambda name: validation[name]["average_precision"])
    selection_pipeline = fitted[selected]
    imp = permutation_importance(selection_pipeline, val[FEATURES], val.late, scoring="average_precision", n_repeats=3, random_state=42, n_jobs=1)
    importance = pd.DataFrame({"feature": FEATURES, "mean_ap_drop": imp.importances_mean, "std_ap_drop": imp.importances_std})
    importance.to_csv(reports/"validation_feature_importance.csv", index=False)
    refit = pd.concat([train, val], ignore_index=True)
    pipeline = clone(models[selected]).fit(refit[FEATURES], refit.late)
    model = CalibratedRiskModel(pipeline).fit_calibrator(cal[FEATURES], cal.late)
    cal_p = model.predict_proba(cal[FEATURES])[:, 1]
    test_p = model.predict_proba(test[FEATURES])[:, 1]
    raw_p = pipeline.predict_proba(test[FEATURES])[:, 1]
    baseline_p = np.repeat(refit.late.mean(), len(test))
    report = {"selection_metric": "validation average precision", "selected_model": selected,
              "validation": validation, "test": metrics(test, test_p), "test_uncalibrated": metrics(test, raw_p),
              "validation_short_promise_rule": capacity_metrics(val, -val.promised_days.to_numpy()),
              "test_constant_prior": metrics(test, baseline_p), "bootstrap_95_percent": day_bootstrap(test, test_p),
              "test_short_promise_rule": capacity_metrics(test, -test.promised_days.to_numpy()),
              "calibration": {"orders": len(cal), "late_rate": float(cal.late.mean()), "slope": float(model.calibrator.coef_[0,0]), "intercept": float(model.calibrator.intercept_[0])},
              "limitations": ["Historical 2017-2018 Brazil data, not current delivery performance.",
                              "Only delivered single-seller orders; no guarantee for cancelled, undelivered or multi-seller orders.",
                              "Features assumed available at approval; source is a final snapshot without update history.",
                              "Outcome-maturity filters and delivered-only selection can underrepresent very slow deliveries.",
                              "Daily top-K is a retrospective next-shift queue, not immediate online intervention.",
                              "Finding late orders does not prove an intervention prevents delays or saves money."]}
    ml_precision = report["test"]["capacity_50"]["precision"]
    rule_precision = report["test_short_promise_rule"]["precision"]
    report["release_gate"] = {
        "status": "research_only",
        "beats_short_promise_rule_at_50": bool(ml_precision > rule_precision),
        "model_precision": ml_precision, "rule_precision": rule_precision,
        "reason": "Historical evaluation only. A baseline comparison is necessary but not sufficient for deployment.",
        "post_test_action": "No model retuning on this test set. The benchmark remains visible; any future development needs a new evaluation plan."
    }
    budget_rows = []
    for budget in [10, 25, 50, 100]:
        for name, scores in [("model", test_p), ("short_promise_rule", -test.promised_days.to_numpy())]:
            r = capacity_metrics(test, scores, budget); r["method"] = name; budget_rows.append(r)
        r = capacity_metrics(test, test_p, budget)
        budget_rows.append({"method": "random", "budget_per_day": budget, "precision": r["random_expected_precision"], "late_found": r["random_expected_late_found"], "selected": r["selected"], "recall": r["random_expected_late_found"]/int(test.late.sum())})
    pd.DataFrame(budget_rows).to_csv(reports/"capacity_comparison.csv", index=False)
    segments = []
    test = test.copy(); test["score"] = test_p
    test["seller_seen"] = np.where(test.seller_id.isin(refit.seller_id), "seen", "unseen")
    test["month"] = test.order_approved_at.dt.strftime("%Y-%m")
    for dimension in ["customer_state", "primary_category", "seller_seen", "month"]:
        for label, group in test.groupby(dimension):
            if len(group) >= 100 and group.late.nunique() == 2:
                r = metrics(group, group.score.to_numpy())
                segments.append({"dimension": dimension, "segment": label, **{k:v for k,v in r.items() if k != "capacity_50"}})
    pd.DataFrame(segments).to_csv(reports/"test_segments.csv", index=False)
    test[["order_id", "order_approved_at", "late", "score"]].to_csv(reports/"predictions_private.csv", index=False)
    # Only synthetic input examples are committed. Real request rows stay local.
    lookup = {r.order_id: r.model_dump(mode="json") for r in requests}
    write_json(reports/"requests_private.json", [lookup[i] for i in test.order_id.head(50)])
    dataset_hash = hashlib.sha256(json.dumps(audit["source_sha256"], sort_keys=True).encode()).hexdigest()
    code_hash = hashlib.sha256(b"".join(p.read_bytes() for p in sorted(Path(__file__).parent.glob("*.py")))).hexdigest()
    version = f"delaylens-1.0-{dataset_hash[:8]}-{code_hash[:8]}"
    metadata = {"model_version": version, "selected_model": selected, "dataset_version": "Olist v2",
                "dataset_sha256": dataset_hash, "code_sha256": code_hash, "features": FEATURES,
                "trained_at_utc": datetime.now(timezone.utc).isoformat(), "python_version": platform.python_version(),
                "packages": {n: importlib.metadata.version(n) for n in ["numpy", "pandas", "scikit-learn", "scipy", "joblib", "pydantic"]},
                "risk_band_thresholds": {"elevated": float(np.quantile(cal_p, .8)), "high": float(np.quantile(cal_p, .95))},
                "risk_band_definition": "80th/95th percentiles of May 2018 calibration scores; not action thresholds.",
                "known_categories": {c: sorted(refit[c].unique().tolist()) for c in CATEGORICAL},
                "numeric_training_ranges": {c: [float(refit[c].min()), float(refit[c].max())] for c in NUMERIC},
                "scope": "Historical single-seller orders, conditional on eventual recorded delivery.",
                "release_gate": report["release_gate"],
                "test_summary": report["test"], "limitations": report["limitations"]}
    joblib.dump(model, artifacts/"model.joblib", compress=3)
    metadata["artifact_sha256"] = hashlib.sha256((artifacts/"model.joblib").read_bytes()).hexdigest()
    write_json(artifacts/"metadata.json", metadata)
    report["model_version"] = version
    report["runtime_seconds"] = time.perf_counter() - started
    write_json(reports/"metrics.json", report)
    make_figures(reports, test, test_p, raw_p, baseline_p, budget_rows, importance)
    print(json.dumps({"selected_model": selected, "test": report["test"], "seconds": report["runtime_seconds"]}, indent=2), flush=True)
    return report


if __name__ == "__main__":
    raise SystemExit("Superseded trainer. Use the reviewed protocol.")

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--output-dir", type=Path, default=Path("."))
    args = parser.parse_args()
    with threadpool_limits(limits=2):
        run(args.data_dir, args.output_dir)
