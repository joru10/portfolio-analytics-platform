from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import PriceRefreshRequest, PriceRefreshResponse
from app.services.pricing import refresh_prices

router = APIRouter(prefix="/v1/prices", tags=["prices"])


@router.post("/refresh", response_model=PriceRefreshResponse)
def refresh_prices_endpoint(request: PriceRefreshRequest, db: Session = Depends(get_db)) -> PriceRefreshResponse:
    effective_date = request.price_date or date.today()

    try:
        result = refresh_prices(db=db, price_date=effective_date, symbols=request.symbols)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return PriceRefreshResponse(
        provider=result.provider,
        price_date=result.price_date,
        requested_count=result.requested_count,
        processed_count=result.processed_count,
        failed_symbols=result.failed_symbols,
        job_run_id=result.job_run_id,
    )
