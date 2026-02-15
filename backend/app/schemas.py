from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class TradeImportRow(BaseModel):
    account: str
    symbol: str
    trade_date: date
    side: str
    quantity: Decimal
    price: Decimal
    fees: Decimal = Decimal("0")
    currency: str = "USD"
    broker_ref: str | None = None


class TradeImportResponse(BaseModel):
    filename: str
    total_rows: int
    imported_rows: int
    duplicate_rows: int
