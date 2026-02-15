from fastapi import FastAPI

from app.api.trades import router as trades_router

app = FastAPI(title="Portfolio Analytics API", version="0.1.0")
app.include_router(trades_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
