from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import MetricsResponse, PositionItem, PositionsResponse
from app.services.portfolio import calculate_positions

router = APIRouter(prefix="/v1", tags=["portfolio"])


@router.get("/positions", response_model=PositionsResponse)
def get_positions(
    snapshot_date: date | None = None,
    account: str | None = None,
    db: Session = Depends(get_db),
) -> PositionsResponse:
    effective_date = snapshot_date or date.today()
    positions = calculate_positions(db=db, snapshot_date=effective_date, account=account)

    return PositionsResponse(
        snapshot_date=effective_date,
        account_filter=account,
        positions=[
            PositionItem(
                account=pos.account,
                symbol=pos.symbol,
                quantity=pos.quantity,
                avg_cost=pos.avg_cost,
                cost_basis=pos.cost_basis,
                market_price=pos.market_price,
                market_value=pos.market_value,
                unrealized_pnl=pos.unrealized_pnl,
                realized_pnl=pos.realized_pnl,
                currency=pos.currency,
            )
            for pos in positions
        ],
    )


@router.get("/metrics", response_model=MetricsResponse)
def get_metrics(
    snapshot_date: date | None = None,
    account: str | None = None,
    db: Session = Depends(get_db),
) -> MetricsResponse:
    effective_date = snapshot_date or date.today()
    positions = calculate_positions(db=db, snapshot_date=effective_date, account=account)

    total_market_value = Decimal("0")
    total_cost_basis = Decimal("0")
    total_unrealized_pnl = Decimal("0")
    total_realized_pnl = Decimal("0")
    gross_exposure = Decimal("0")
    net_exposure = Decimal("0")
    symbols_priced = 0

    for pos in positions:
        total_cost_basis += pos.cost_basis
        total_realized_pnl += pos.realized_pnl

        if pos.market_value is not None:
            symbols_priced += 1
            total_market_value += pos.market_value
            net_exposure += pos.market_value
            gross_exposure += abs(pos.market_value)

        if pos.unrealized_pnl is not None:
            total_unrealized_pnl += pos.unrealized_pnl

    return MetricsResponse(
        snapshot_date=effective_date,
        account_filter=account,
        total_positions=len(positions),
        symbols_priced=symbols_priced,
        symbols_unpriced=len(positions) - symbols_priced,
        total_market_value=total_market_value,
        total_cost_basis=total_cost_basis,
        total_unrealized_pnl=total_unrealized_pnl,
        total_realized_pnl=total_realized_pnl,
        gross_exposure=gross_exposure,
        net_exposure=net_exposure,
    )
