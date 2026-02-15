from app.config import settings
from app.market_data.base import MarketDataProvider
from app.market_data.providers.demo import DemoMarketDataProvider
from app.market_data.providers.yfinance_provider import YFinanceMarketDataProvider

AVAILABLE_PROVIDERS = ("demo", "yfinance")


def get_market_data_provider(provider_name: str | None = None) -> MarketDataProvider:
    provider = (provider_name or settings.market_data_provider).strip().lower()

    if provider == "demo":
        return DemoMarketDataProvider()
    if provider == "yfinance":
        return YFinanceMarketDataProvider()

    raise ValueError(f"Unsupported market data provider: {provider}")


def resolve_provider_chain(requested_providers: list[str] | None = None) -> list[str]:
    if requested_providers:
        chain = [p.strip().lower() for p in requested_providers if p.strip()]
    else:
        chain = [settings.market_data_provider.strip().lower()]

    invalid = [p for p in chain if p not in AVAILABLE_PROVIDERS]
    if invalid:
        raise ValueError(f"Unsupported market data provider(s): {', '.join(invalid)}")

    # preserve order, remove duplicates
    deduped: list[str] = []
    seen: set[str] = set()
    for p in chain:
        if p not in seen:
            seen.add(p)
            deduped.append(p)
    return deduped
