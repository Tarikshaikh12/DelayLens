"""Join Olist tables without multiplying orders; preserve a cleaning audit."""
import hashlib
import json
from pathlib import Path
import pandas as pd
from pydantic import ValidationError
from .schema import OrderInput
from .features import feature_frame

FILES = ["olist_orders_dataset.csv", "olist_order_items_dataset.csv",
         "olist_customers_dataset.csv", "olist_sellers_dataset.csv",
         "olist_products_dataset.csv", "product_category_name_translation.csv"]


def read_unique(path, key):
    df = pd.read_csv(path)
    if df.duplicated(key).any():
        raise ValueError(f"Duplicate key {key} in {path.name}; inspect the source instead of guessing.")
    return df


def build_dataset(raw_dir: Path):
    raw_dir = Path(raw_dir)
    for name in FILES:
        if not (raw_dir / name).exists():
            raise FileNotFoundError(f"Missing {name}. Run python scripts/download_data.py first.")
    orders = read_unique(raw_dir / FILES[0], "order_id")
    items = read_unique(raw_dir / FILES[1], ["order_id", "order_item_id"])
    customers = read_unique(raw_dir / FILES[2], "customer_id")
    sellers = read_unique(raw_dir / FILES[3], "seller_id")
    products = read_unique(raw_dir / FILES[4], "product_id")
    translation = read_unique(raw_dir / FILES[5], "product_category_name")
    audit = {"raw_orders": len(orders), "status_counts": orders.order_status.value_counts().to_dict(),
             "source_sha256": {f: hashlib.sha256((raw_dir / f).read_bytes()).hexdigest() for f in FILES},
             "exclusions": {}}
    for col in ["order_purchase_timestamp", "order_approved_at", "order_estimated_delivery_date", "order_delivered_customer_date"]:
        orders[col] = pd.to_datetime(orders[col], errors="coerce")

    def keep(mask, reason):
        nonlocal orders
        audit["exclusions"][reason] = int((~mask).sum())
        orders = orders.loc[mask].copy()

    needed = ["order_purchase_timestamp", "order_approved_at", "order_estimated_delivery_date"]
    keep(orders[needed].notna().all(axis=1), "missing_required_timestamp")
    counts = items.groupby("order_id").seller_id.nunique()
    keep(orders.order_id.map(counts).eq(1), "not_exactly_one_seller")

    joined = items.merge(products, on="product_id", how="left", validate="many_to_one")
    joined = joined.merge(translation, on="product_category_name", how="left", validate="many_to_one")
    joined["category"] = joined.product_category_name_english.fillna("unknown")
    joined["volume"] = joined.product_length_cm * joined.product_height_cm * joined.product_width_cm
    joined["weight"] = joined.product_weight_g.where(joined.product_weight_g > 0)
    joined["volume"] = joined.volume.where(joined.volume > 0)
    # A partial weight sum would pretend missing items weigh zero. Keep it unknown.
    def complete_sum(x):
        return x.sum() if x.notna().all() else float("nan")
    agg = joined.groupby("order_id").agg(
        seller_id=("seller_id", "first"), item_count=("order_item_id", "size"),
        total_price_brl=("price", "sum"), freight_brl=("freight_value", "sum"),
        total_weight_g=("weight", complete_sum), total_volume_cm3=("volume", complete_sum))
    cats = joined.groupby(["order_id", "category"], as_index=False).price.sum()
    primary = cats.sort_values(["order_id", "price", "category"], ascending=[True, False, True]).drop_duplicates("order_id")
    agg = agg.merge(primary[["order_id", "category"]], on="order_id", validate="one_to_one")
    agg = agg.merge(sellers[["seller_id", "seller_state"]], on="seller_id", how="left", validate="many_to_one")
    orders = orders.merge(agg, on="order_id", how="left", validate="one_to_one")
    orders = orders.merge(customers[["customer_id", "customer_state"]], on="customer_id", how="left", validate="many_to_one")
    records, valid_rows, invalid = [], [], []
    for row in orders.to_dict("records"):
        values = {k: row[k] for k in ["order_id", "customer_state", "seller_state", "item_count", "total_price_brl", "freight_brl"]}
        values.update(purchased_at=row["order_purchase_timestamp"], approved_at=row["order_approved_at"],
                      promised_date=row["order_estimated_delivery_date"].date(), primary_category=row["category"])
        for name in ["total_weight_g", "total_volume_cm3"]:
            values[name] = None if pd.isna(row[name]) else float(row[name])
        try:
            records.append(OrderInput(**values))
            valid_rows.append(row)
        except ValidationError as e:
            invalid.append({"order_id": row["order_id"], "reason": str(e)})
    meta = pd.DataFrame(valid_rows)
    # Calendar-date comparison: a delivery at 18:00 on its promised day is ON TIME.
    valid_delivery = meta.order_delivered_customer_date.ge(meta.order_approved_at)
    meta["late"] = (meta.order_delivered_customer_date.dt.normalize() > meta.order_estimated_delivery_date.dt.normalize()).astype(float).where(valid_delivery)
    X = feature_frame(records)
    dataset = pd.concat([meta[["order_id", "seller_id", "order_approved_at", "order_delivered_customer_date", "order_estimated_delivery_date", "order_status", "late"]].reset_index(drop=True), X], axis=1)
    audit["exclusions"]["input_contract_failure"] = len(invalid)
    audit["eligible_orders"] = len(dataset)
    audit["observed_late_rate"] = float(dataset.late.mean())
    audit["unknown_outcomes"] = int(dataset.late.isna().sum())
    audit["invalid_delivery_before_approval"] = int(meta.order_delivered_customer_date.lt(meta.order_approved_at).sum())
    audit["missing_features"] = X.isna().sum().to_dict()
    assert len(dataset) + sum(audit["exclusions"].values()) == audit["raw_orders"]
    assert dataset.order_id.is_unique
    return dataset, records, audit


def temporal_split(df):
    """Fixed windows and outcome-maturity gaps decided before model fitting.

    Labels used for training/selection/calibration must be observed BEFORE the
    next decision stage. The delivered-only cohort still has selection bias.
    """
    windows = {
        "train": ("2017-01-01", "2018-01-01", "2018-03-01"),
        "validation": ("2018-03-01", "2018-04-01", "2018-05-01"),
        "calibration": ("2018-05-01", "2018-06-01", "2018-07-01"),
        "test": ("2018-07-01", "2018-09-01", None),
    }
    parts, summary = {}, {}
    for name, (start, end, available_before) in windows.items():
        mask = df.order_approved_at.ge(start) & df.order_approved_at.lt(end)
        candidate = df.loc[mask]
        part = candidate if available_before is None else candidate.loc[candidate.order_delivered_customer_date.lt(available_before)]
        if part.empty or part.late.nunique() < 2:
            raise ValueError(f"{name} needs both classes; check dataset/version/window.")
        parts[name] = part.copy().reset_index(drop=True)
        summary[name] = {"approval_start": start, "approval_end_exclusive": end,
                         "labels_observed_before": available_before, "orders": len(part),
                         "excluded_unmatured": len(candidate) - len(part), "late_rate": float(part.late.mean())}
    ids = [set(p.order_id) for p in parts.values()]
    assert sum(map(len, ids)) == len(set.union(*ids))
    summary["unused_eligible_orders"] = len(df) - sum(len(x) for x in parts.values())
    return parts, summary
