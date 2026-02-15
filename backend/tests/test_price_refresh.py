from app.models import JobRun, PriceEOD


def test_price_refresh_from_traded_symbols_is_idempotent(client, db_session) -> None:
    csv_content = """account,symbol,trade_date,side,quantity,price,fees,currency,broker_ref
ACC1,AAPL,2026-02-10,BUY,2,100,0,USD,T1
ACC1,MSFT,2026-02-10,BUY,3,100,0,USD,T2
"""
    import_resp = client.post("/v1/trades/import", files={"file": ("seed.csv", csv_content, "text/csv")})
    assert import_resp.status_code == 200

    payload = {"price_date": "2026-02-14", "symbols": []}
    first = client.post("/v1/prices/refresh", json=payload)
    assert first.status_code == 200
    assert first.json()["requested_count"] == 2
    assert first.json()["processed_count"] == 2
    assert first.json()["failed_symbols"] == []
    assert first.json()["providers_used"] == ["demo"]

    second = client.post("/v1/prices/refresh", json=payload)
    assert second.status_code == 200
    assert second.json()["processed_count"] == 2

    price_rows = db_session.query(PriceEOD).all()
    assert len(price_rows) == 2

    run_rows = db_session.query(JobRun).all()
    assert len(run_rows) == 2


def test_price_refresh_tracks_provider_failures(client) -> None:
    payload = {"price_date": "2026-02-14", "symbols": ["AAPL", "XFAIL_BAD"]}
    response = client.post("/v1/prices/refresh", json=payload)

    assert response.status_code == 200
    assert response.json()["requested_count"] == 2
    assert response.json()["processed_count"] == 1
    assert response.json()["failed_symbols"] == ["XFAIL_BAD"]


def test_price_refresh_rejects_unknown_provider(client) -> None:
    response = client.post(
        "/v1/prices/refresh",
        json={"price_date": "2026-02-14", "symbols": ["AAPL"], "providers": ["unknown"]},
    )
    assert response.status_code == 400
    assert "Unsupported market data provider" in response.json()["detail"]


def test_price_refresh_provider_fallback_chain(client) -> None:
    response = client.post(
        "/v1/prices/refresh",
        json={"price_date": "2026-02-14", "symbols": ["XFAIL_BAD", "AAPL"], "providers": ["demo", "yfinance"]},
    )

    assert response.status_code == 200
    assert response.json()["requested_count"] == 2
    assert response.json()["processed_count"] >= 1
    assert response.json()["providers_used"] == ["demo", "yfinance"]
