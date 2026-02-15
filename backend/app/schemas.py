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


class PositionItem(BaseModel):
    account: str
    symbol: str
    quantity: Decimal
    avg_cost: Decimal
    cost_basis: Decimal
    market_price: Decimal | None
    market_value: Decimal | None
    unrealized_pnl: Decimal | None
    realized_pnl: Decimal
    currency: str


class PositionsResponse(BaseModel):
    snapshot_date: date
    account_filter: str | None
    positions: list[PositionItem]


class MetricsResponse(BaseModel):
    snapshot_date: date
    account_filter: str | None
    total_positions: int
    symbols_priced: int
    symbols_unpriced: int
    total_market_value: Decimal
    total_cost_basis: Decimal
    total_unrealized_pnl: Decimal
    total_realized_pnl: Decimal
    gross_exposure: Decimal
    net_exposure: Decimal
