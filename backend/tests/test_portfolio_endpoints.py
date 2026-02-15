from datetime import date
from decimal import Decimal

from app.models import PriceEOD


def _d(value: str | float | int) -> Decimal:
    return Decimal(str(value))


def test_positions_and_metrics_with_snapshot_pricing(client, db_session) -> None:
    csv_content = """account,symbol,trade_date,side,quantity,price,fees,currency,broker_ref
ACC1,AAPL,2026-02-10,BUY,10,100,0,USD,T1
ACC1,AAPL,2026-02-11,SELL,4,120,0,USD,T2
ACC1,MSFT,2026-02-12,BUY,5,50,0,USD,T3
ACC1,GOOG,2026-02-12,BUY,2,10,0,USD,T4
"""
    import_resp = client.post("/v1/trades/import", files={"file": ("trades.csv", csv_content, "text/csv")})
    assert import_resp.status_code == 200

    db_session.add_all(
        [
            PriceEOD(symbol="AAPL", price_date=date(2026, 2, 13), close_price=_d("125"), currency="USD", source="test"),
            PriceEOD(symbol="AAPL", price_date=date(2026, 2, 14), close_price=_d("130"), currency="USD", source="test"),
            PriceEOD(symbol="AAPL", price_date=date(2026, 2, 15), close_price=_d("140"), currency="USD", source="test"),
            PriceEOD(symbol="MSFT", price_date=date(2026, 2, 14), close_price=_d("40"), currency="USD", source="test"),
        ]
    )
    db_session.commit()

    positions_resp = client.get("/v1/positions", params={"snapshot_date": "2026-02-14"})
    assert positions_resp.status_code == 200
    positions_payload = positions_resp.json()

    assert positions_payload["snapshot_date"] == "2026-02-14"
    assert len(positions_payload["positions"]) == 3

    by_symbol = {row["symbol"]: row for row in positions_payload["positions"]}
    assert _d(by_symbol["AAPL"]["quantity"]) == _d("6")
    assert _d(by_symbol["AAPL"]["avg_cost"]) == _d("100")
    assert _d(by_symbol["AAPL"]["market_price"]) == _d("130")
    assert _d(by_symbol["AAPL"]["market_value"]) == _d("780")
    assert _d(by_symbol["AAPL"]["realized_pnl"]) == _d("80")
    assert _d(by_symbol["AAPL"]["unrealized_pnl"]) == _d("180")

    assert by_symbol["GOOG"]["market_price"] is None
    assert by_symbol["GOOG"]["market_value"] is None

    metrics_resp = client.get("/v1/metrics", params={"snapshot_date": "2026-02-14"})
    assert metrics_resp.status_code == 200
    metrics_payload = metrics_resp.json()

    assert metrics_payload["total_positions"] == 3
    assert metrics_payload["symbols_priced"] == 2
    assert metrics_payload["symbols_unpriced"] == 1
    assert _d(metrics_payload["total_market_value"]) == _d("980")
    assert _d(metrics_payload["total_cost_basis"]) == _d("870")
    assert _d(metrics_payload["total_unrealized_pnl"]) == _d("130")
    assert _d(metrics_payload["total_realized_pnl"]) == _d("80")
    assert _d(metrics_payload["gross_exposure"]) == _d("980")
    assert _d(metrics_payload["net_exposure"]) == _d("980")


def test_metrics_account_filter_scopes_positions(client, db_session) -> None:
    csv_content = """account,symbol,trade_date,side,quantity,price,fees,currency,broker_ref
ACC1,AAPL,2026-02-10,BUY,2,100,0,USD,T1
ACC2,AAPL,2026-02-10,BUY,3,100,0,USD,T2
"""
    import_resp = client.post("/v1/trades/import", files={"file": ("accounts.csv", csv_content, "text/csv")})
    assert import_resp.status_code == 200

    db_session.add(PriceEOD(symbol="AAPL", price_date=date(2026, 2, 10), close_price=_d("110"), currency="USD", source="test"))
    db_session.commit()

    metrics_resp = client.get("/v1/metrics", params={"snapshot_date": "2026-02-10", "account": "ACC2"})
    assert metrics_resp.status_code == 200
    payload = metrics_resp.json()

    assert payload["total_positions"] == 1
    assert _d(payload["total_market_value"]) == _d("330")
    assert _d(payload["total_cost_basis"]) == _d("300")
    assert _d(payload["total_unrealized_pnl"]) == _d("30")
