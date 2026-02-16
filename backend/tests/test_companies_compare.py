def test_compare_companies_works_without_trades(client) -> None:
    response = client.post(
        "/v1/companies/compare",
        json={
            "symbols": ["AAPL", "MSFT"],
            "start_date": "2026-01-05",
            "end_date": "2026-01-12",
            "providers": ["demo"],
        },
    )
    assert response.status_code == 200

    payload = response.json()
    assert payload["symbols"] == ["AAPL", "MSFT"]
    assert payload["providers_used"] == ["demo"]
    assert payload["failed_symbols"] == []
    assert len(payload["series"]) > 0

    by_symbol = {item["symbol"]: item for item in payload["summary"]}
    assert set(by_symbol.keys()) == {"AAPL", "MSFT"}
    assert by_symbol["AAPL"]["observations"] > 0
    assert by_symbol["MSFT"]["observations"] > 0


def test_compare_companies_invalid_provider_returns_400(client) -> None:
    response = client.post(
        "/v1/companies/compare",
        json={
            "symbols": ["AAPL", "MSFT"],
            "start_date": "2026-01-05",
            "end_date": "2026-01-12",
            "providers": ["unknown"],
        },
    )
    assert response.status_code == 400
    assert "Unsupported market data provider" in response.json()["detail"]


def test_compare_companies_requires_symbol(client) -> None:
    response = client.post(
        "/v1/companies/compare",
        json={"symbols": [], "start_date": "2026-01-05", "end_date": "2026-01-12", "providers": ["demo"]},
    )
    assert response.status_code == 400
    assert "At least one symbol is required" in response.json()["detail"]
