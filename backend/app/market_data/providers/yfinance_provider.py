from datetime import date, timedelta
from decimal import Decimal

import yfinance as yf

from app.market_data.base import PricePoint


class YFinanceMarketDataProvider:
    def fetch_eod(self, symbols: list[str], as_of_date: date) -> tuple[list[PricePoint], list[str]]:
        points: list[PricePoint] = []
        failed: list[str] = []

        start = as_of_date - timedelta(days=15)
        end = as_of_date + timedelta(days=1)

        for symbol in symbols:
            clean = symbol.strip().upper()
            if not clean:
                continue
            try:
                history = yf.Ticker(clean).history(start=start.isoformat(), end=end.isoformat(), auto_adjust=False)
                if history.empty:
                    failed.append(clean)
                    continue

                history = history[history.index.date <= as_of_date]
                if history.empty:
                    failed.append(clean)
                    continue

                close = history.iloc[-1]["Close"]
                if close is None:
                    failed.append(clean)
                    continue

                points.append(
                    PricePoint(
                        symbol=clean,
                        price_date=as_of_date,
                        close_price=Decimal(str(float(close))),
                        currency="USD",
                    )
                )
            except Exception:
                failed.append(clean)

        return points, failed

    def fetch_history(self, symbols: list[str], start_date: date, end_date: date) -> tuple[list[PricePoint], list[str]]:
        points: list[PricePoint] = []
        failed: list[str] = []

        fetch_end = end_date + timedelta(days=1)

        for symbol in symbols:
            clean = symbol.strip().upper()
            if not clean:
                continue
            try:
                history = yf.Ticker(clean).history(start=start_date.isoformat(), end=fetch_end.isoformat(), auto_adjust=False)
                if history.empty:
                    failed.append(clean)
                    continue

                if "Close" not in history.columns:
                    failed.append(clean)
                    continue

                for idx, row in history.iterrows():
                    dt = idx.date()
                    if dt < start_date or dt > end_date:
                        continue
                    close = row.get("Close")
                    if close is None:
                        continue
                    points.append(
                        PricePoint(
                            symbol=clean,
                            price_date=dt,
                            close_price=Decimal(str(float(close))),
                            currency="USD",
                        )
                    )
            except Exception:
                failed.append(clean)

        return points, failed
