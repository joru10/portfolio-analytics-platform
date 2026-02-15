from app.config import settings
from app.market_data.base import MarketDataProvider
from app.market_data.providers.demo import DemoMarketDataProvider



def get_market_data_provider() -> MarketDataProvider:
    provider = settings.market_data_provider.strip().lower()

    if provider == "demo":
        return DemoMarketDataProvider()

    raise ValueError(f"Unsupported market data provider: {settings.market_data_provider}")
