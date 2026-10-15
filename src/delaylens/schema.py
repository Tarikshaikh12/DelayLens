"""The approval-time input contract, shared by training and the API."""
from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

State = Literal["AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"]


class OrderInput(BaseModel):
    """One order from one seller. Money is BRL; timestamps are local and naive.

    Category is the English Olist category with the largest summed item price.
    Missing total weight/volume means at least one item's measurement is unknown.
    """
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    order_id: str = Field(min_length=1, max_length=80, pattern=r"^[A-Za-z0-9_-]+$")
    purchased_at: datetime
    approved_at: datetime
    promised_date: date
    customer_state: State
    seller_state: State
    primary_category: str = Field(min_length=1, max_length=80, pattern=r"^[a-z0-9_]+$")
    item_count: int = Field(ge=1, le=100, strict=True)
    total_price_brl: float = Field(gt=0, le=100000)
    freight_brl: float = Field(ge=0, le=100000)
    total_weight_g: float | None = Field(default=None, gt=0, le=1000000)
    total_volume_cm3: float | None = Field(default=None, gt=0, le=1000000000)

    @model_validator(mode="after")
    def dates_make_sense(self):
        if self.purchased_at.tzinfo or self.approved_at.tzinfo:
            raise ValueError("Use local timestamps without UTC offsets, as in the Olist source.")
        hours = (self.approved_at - self.purchased_at).total_seconds() / 3600
        if not 0 <= hours <= 720:
            raise ValueError("Approval must be between purchase time and 30 days after purchase.")
        days = (self.promised_date - self.approved_at.date()).days
        if not 0 <= days <= 120:
            raise ValueError("The promised date must be 0 to 120 days after approval.")
        return self


class BatchInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    orders: list[OrderInput] = Field(min_length=1, max_length=500)
    investigation_budget: int = Field(default=50, ge=1, le=500, strict=True)

    @model_validator(mode="after")
    def unique_ids(self):
        ids = [o.order_id for o in self.orders]
        if len(ids) != len(set(ids)):
            raise ValueError("order_id must be unique within a batch.")
        return self
