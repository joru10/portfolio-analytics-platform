from datetime import date
from decimal import Decimal

from app.models import PriceEOD


def test_analytics_endpoint_returns_risk_and_series(client, db_session) -> None:
    csv_content = """account,symbol,trade_date,side,quantity,price,fees,currency,broker_ref
ACC1,AAPL,2026-02-10,BUY,10,100,0,USD,T1
ACC1,MSFT,2026-02-10,BUY,5,50,0,USD,T2
ACC1,AAPL,2026-02-12,SELL,2,120,0,USD,T3
"""
    import_resp = client.post("/v1/trades/import", files={"file": ("analytics.csv", csv_content, "text/csv")})
    assert import_resp.status_code == 200

    prices = [
        PriceEOD(symbol="AAPL", price_date=date(2026, 2, 10), close_price=Decimal("100"), currency="USD", source="test"),
        PriceEOD(symbol="MSFT", price_date=date(2026, 2, 10), close_price=Decimal("50"), currency="USD", source="test"),
        PriceEOD(symbol="AAPL", price_date=date(2026, 2, 11), close_price=Decimal("102"), currency="USD", source="test"),
        PriceEOD(symbol="MSFT", price_date=date(2026, 2, 11), close_price=Decimal("52"), currency="USD", source="test"),
        PriceEOD(symbol="AAPL", price_date=date(2026, 2, 12), close_price=Decimal("105"), currency="USD", source="test"),
        PriceEOD(symbol="MSFT", price_date=date(2026, 2, 12), close_price=Decimal("48"), currency="USD", source="test"),
        PriceEOD(symbol="AAPL", price_date=date(2026, 2, 13), close_price=Decimal("108"), currency="USD", source="test"),
        PriceEOD(symbol="MSFT", price_date=date(2026, 2, 13), close_price=Decimal("49"), currency="USD", source="test"),
    ]
    db_session.add_all(prices)
    db_session.commit()

    response = client.get(
        "/v1/analytics",
        params={"start_date": "2026-02-10", "snapshot_date": "2026-02-13", "account": "ACC1"},
    )
    assert response.status_code == 200

    payload = response.json()
    assert payload["snapshot_date"] == "2026-02-13"
    assert payload["start_date"] == "2026-02-10"
    assert isinstance(payload["series"], list)
    assert len(payload["series"]) >= 3

    # Risk fields should be present and numeric.
    assert isinstance(payload["annualized_volatility"], float)
    assert isinstance(payload["sharpe_ratio"], float)
    assert isinstance(payload["max_drawdown"], float)
    assert isinstance(payload["var_95"], float)
    assert isinstance(payload["cvar_95"], float)

    assert payload["concentration_top_symbol"] in {"AAPL", "MSFT"}
    assert 0 <= payload["concentration_top_weight"] <= 1
