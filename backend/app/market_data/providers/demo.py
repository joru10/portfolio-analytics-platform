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

    def fetch_history(self, symbols: list[str], start_date: date, end_date: date) -> tuple[list[PricePoint], list[str]]:
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
            current = start_date
            while current <= end_date:
                if current.weekday() < 5:
                    day_bias = (current.toordinal() % 30) - 15
                    price = Decimal(seed % 200 + 20) + Decimal(day_bias) / Decimal("20")
                    points.append(
                        PricePoint(
                            symbol=clean,
                            price_date=current,
                            close_price=price,
                            currency="USD",
                        )
                    )
                current = date.fromordinal(current.toordinal() + 1)

        return points, failed
