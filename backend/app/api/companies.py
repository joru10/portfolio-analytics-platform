from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import (
    CompanyCompareRequest,
    CompanyCompareResponse,
    CompanySymbolSearchItem,
    CompanySymbolSearchResponse,
)
from app.services.companies import compare_companies, search_company_symbols

router = APIRouter(prefix="/v1/companies", tags=["companies"])


@router.post("/compare", response_model=CompanyCompareResponse)
def compare_companies_endpoint(request: CompanyCompareRequest, db: Session = Depends(get_db)) -> CompanyCompareResponse:
    effective_end = request.end_date or date.today()
    effective_start = request.start_date or (effective_end - timedelta(days=180))

    try:
        result = compare_companies(
            db=db,
            symbols=request.symbols,
            start_date=effective_start,
            end_date=effective_end,
            providers=request.providers,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return CompanyCompareResponse(
        start_date=result.start_date,
        end_date=result.end_date,
        symbols=result.symbols,
        providers_used=result.providers_used,
        failed_symbols=result.failed_symbols,
        series=[
            {
                "date": point.date,
                "prices": point.prices,
                "normalized": point.normalized,
            }
            for point in result.series
        ],
        summary=[
            {
                "symbol": item.symbol,
                "start_price": item.start_price,
                "end_price": item.end_price,
                "return_pct": item.return_pct,
                "annualized_volatility": item.annualized_volatility,
                "max_drawdown": item.max_drawdown,
                "observations": item.observations,
            }
            for item in result.summary
        ],
        correlation=result.correlation,
    )


@router.get("/search", response_model=CompanySymbolSearchResponse)
def search_companies_endpoint(q: str = Query(..., min_length=2, max_length=80)) -> CompanySymbolSearchResponse:
    try:
        items = search_company_symbols(q)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Symbol search provider unavailable",
        ) from exc

    return CompanySymbolSearchResponse(
        query=q,
        items=[
            CompanySymbolSearchItem(
                symbol=item.symbol,
                name=item.name,
                exchange=item.exchange,
                quote_type=item.quote_type,
            )
            for item in items
        ],
    )
