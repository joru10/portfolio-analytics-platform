from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.ai import router as ai_router
from app.api.companies import router as companies_router
from app.api.portfolio import router as portfolio_router
from app.api.prices import router as prices_router
from app.api.trades import router as trades_router
from app.config import settings

app = FastAPI(title="Portfolio Analytics API", version="0.1.0")

allowed_origins = [origin.strip() for origin in settings.cors_allow_origins.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(trades_router)
app.include_router(portfolio_router)
app.include_router(prices_router)
app.include_router(companies_router)
app.include_router(ai_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


frontend_dir = Path(__file__).resolve().parents[2] / "frontend"
if (frontend_dir / "index.html").exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
