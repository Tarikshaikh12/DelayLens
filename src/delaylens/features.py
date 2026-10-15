"""Explicit allowlist: no status, actual delivery, reviews, IDs or future history."""
import numpy as np
import pandas as pd
from .schema import OrderInput

NUMERIC = ["promised_days", "approval_hours", "item_count", "total_price_brl",
           "freight_brl", "total_weight_g", "total_volume_cm3", "freight_ratio",
           "average_item_price", "same_state", "approval_weekday", "approval_hour",
           "month_sin", "month_cos"]
CATEGORICAL = ["customer_state", "seller_state", "primary_category"]
FEATURES = NUMERIC + CATEGORICAL


def feature_row(order: OrderInput) -> dict:
    month_angle = 2 * np.pi * (order.approved_at.month - 1) / 12
    row = {k: getattr(order, k) for k in ["item_count", "total_price_brl", "freight_brl",
           "total_weight_g", "total_volume_cm3", *CATEGORICAL]}
    row.update(
        promised_days=(order.promised_date - order.approved_at.date()).days,
        approval_hours=(order.approved_at - order.purchased_at).total_seconds() / 3600,
        freight_ratio=order.freight_brl / order.total_price_brl,
        average_item_price=order.total_price_brl / order.item_count,
        same_state=int(order.customer_state == order.seller_state),
        approval_weekday=order.approved_at.weekday(), approval_hour=order.approved_at.hour,
        month_sin=float(np.sin(month_angle)), month_cos=float(np.cos(month_angle)),
    )
    return row


def feature_frame(orders: list[OrderInput]) -> pd.DataFrame:
    frame = pd.DataFrame([feature_row(o) for o in orders], columns=FEATURES)
    frame[NUMERIC] = frame[NUMERIC].astype(float)
    return frame
