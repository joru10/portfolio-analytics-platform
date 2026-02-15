from datetime import date
from decimal import Decimal

from app.market_data.base import PricePoint


class DemoMarketDataProvider:
    def fetch_eod(self, symbols: list[str], as_of_date: date) -> tuple[list[PricePoint], list[str]]:
        points: list[PricePoint] = []
        failed: list[str] = []

        for symbol in symbols:
            clean = symbol.strip().upper()
            if not clean:
                continue
            if clean.startswith("XFAIL"):
                failed.append(clean)
                continue

            seed = sum(ord(char) for char in clean)
            price = Decimal(seed % 200 + 20) + Decimal("0.25")
            points.append(
                PricePoint(
                    symbol=clean,
                    price_date=as_of_date,
                    close_price=price,
                    currency="USD",
                )
            )

        return points, failed
