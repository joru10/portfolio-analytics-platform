from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Protocol


@dataclass
class PricePoint:
    symbol: str
    price_date: date
    close_price: Decimal
    currency: str


class MarketDataProvider(Protocol):
    def fetch_eod(self, symbols: list[str], as_of_date: date) -> tuple[list[PricePoint], list[str]]:
        ...
