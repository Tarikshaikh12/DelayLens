"""Ranking, probability and daily-capacity metrics, with deterministic ties."""
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score, brier_score_loss, log_loss


def queue_table(meta, scores, budget=50):
    table = meta[["order_id", "order_approved_at", "late"]].copy()
    table["day"] = table.order_approved_at.dt.strftime("%Y-%m-%d")
    table["score"] = scores
    table = table.sort_values(["day", "score", "order_id"], ascending=[True, False, True])
    table["selected"] = table.groupby("day").cumcount() < budget
    return table


def capacity_metrics(meta, scores, budget=50):
    q = queue_table(meta, scores, budget)
    n = int(q.selected.sum())
    hits = int(q.loc[q.selected, "late"].sum())
    daily = q.groupby("day").agg(orders=("late", "size"), late=("late", "sum"), selected=("selected", "sum"))
    random_hits = float((daily.selected * daily.late / daily.orders).sum())
    return {"budget_per_day": budget, "selected": n, "late_found": hits,
            "precision": hits / n if n else 0.0,
            "recall": hits / int(q.late.sum()) if q.late.sum() else 0.0,
            "random_expected_late_found": random_hits,
            "random_expected_precision": random_hits / n if n else 0.0,
            "lift_over_random": hits / random_hits if random_hits else None}


def metrics(meta, probabilities):
    y = meta.late.to_numpy()
    return {"orders": len(y), "late_orders": int(y.sum()), "late_rate": float(y.mean()),
            "average_precision": float(average_precision_score(y, probabilities)),
            "roc_auc": float(roc_auc_score(y, probabilities)),
            "brier_score": float(brier_score_loss(y, probabilities)),
            "log_loss": float(log_loss(y, probabilities, labels=[0, 1])),
            "capacity_50": capacity_metrics(meta, probabilities, 50)}


def day_bootstrap(meta, probabilities, repetitions=300, seed=42):
    """Resample entire approval days, not independent orders. Model stays fixed."""
    q = queue_table(meta, probabilities)
    groups = list(q.groupby("day", sort=True))
    arrays = [(g.late.to_numpy(), g.score.to_numpy(), int(g.selected.sum()),
               int(g.loc[g.selected, "late"].sum()), float(min(50, len(g)) * g.late.mean())) for _, g in groups]
    rng, values = np.random.default_rng(seed), []
    for _ in range(repetitions):
        sampled = [arrays[i] for i in rng.integers(0, len(arrays), len(arrays))]
        y, p = np.concatenate([a[0] for a in sampled]), np.concatenate([a[1] for a in sampled])
        if len(np.unique(y)) < 2:
            continue
        selected, hits, expected = sum(a[2] for a in sampled), sum(a[3] for a in sampled), sum(a[4] for a in sampled)
        values.append([average_precision_score(y, p), hits / selected, hits / y.sum(), hits / expected])
    result = {"method": "300 whole-day bootstrap samples, fixed fitted model", "replicates": len(values)}
    for i, name in enumerate(["average_precision", "precision_at_50_per_day", "recall_at_50_per_day", "lift_at_50_per_day"]):
        result[name] = [float(x) for x in np.quantile(np.asarray(values)[:, i], [.025, .975])]
    return result
