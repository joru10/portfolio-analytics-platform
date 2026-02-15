def test_import_trades_csv_idempotent(client) -> None:
    csv_content = """account,symbol,trade_date,side,quantity,price,fees,currency,broker_ref
ACC1,AAPL,2026-02-14,BUY,10,185.5,1.2,USD,BRK-1
ACC1,MSFT,2026-02-14,SELL,5,410.0,0.5,USD,BRK-2
"""

    files = {"file": ("trades.csv", csv_content, "text/csv")}
    first = client.post("/v1/trades/import", files=files)

    assert first.status_code == 200
    assert first.json()["total_rows"] == 2
    assert first.json()["imported_rows"] == 2
    assert first.json()["duplicate_rows"] == 0

    second = client.post("/v1/trades/import", files=files)

    assert second.status_code == 200
    assert second.json()["total_rows"] == 2
    assert second.json()["imported_rows"] == 0
    assert second.json()["duplicate_rows"] == 2


def test_import_trades_rejects_invalid_rows(client) -> None:
    bad_csv = """account,symbol,trade_date,side,quantity,price
ACC1,AAPL,2026-02-14,HOLD,10,185.5
"""

    response = client.post("/v1/trades/import", files={"file": ("bad.csv", bad_csv, "text/csv")})

    assert response.status_code == 422
    assert "BUY or SELL" in response.json()["detail"]
