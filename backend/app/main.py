from fastapi import FastAPI

from app.api.portfolio import router as portfolio_router
from app.api.prices import router as prices_router
from app.api.trades import router as trades_router

app = FastAPI(title="Portfolio Analytics API", version="0.1.0")
app.include_router(trades_router)
app.include_router(portfolio_router)
app.include_router(prices_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
