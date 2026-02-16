from app.api import companies as companies_api
from app.services.companies import SymbolSearchItem


def test_company_search_returns_items(client, monkeypatch) -> None:
    def fake_search(query: str, limit: int = 10):
        assert query == "blaize"
        return [
            SymbolSearchItem(symbol="BZAI", name="Blaize Holdings", exchange="NMS", quote_type="EQUITY"),
            SymbolSearchItem(symbol="AAPL", name="Apple Inc.", exchange="NMS", quote_type="EQUITY"),
        ]

    monkeypatch.setattr(companies_api, "search_company_symbols", fake_search)

    response = client.get("/v1/companies/search", params={"q": "blaize"})
    assert response.status_code == 200
    payload = response.json()

    assert payload["query"] == "blaize"
    assert payload["items"][0]["symbol"] == "BZAI"
    assert payload["items"][0]["name"] == "Blaize Holdings"


def test_company_search_provider_failure_returns_502(client, monkeypatch) -> None:
    def failing_search(query: str, limit: int = 10):
        raise RuntimeError("upstream down")

    monkeypatch.setattr(companies_api, "search_company_symbols", failing_search)

    response = client.get("/v1/companies/search", params={"q": "apple"})
    assert response.status_code == 502
    assert response.json()["detail"] == "Symbol search provider unavailable"
