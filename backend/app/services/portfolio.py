from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.models import PriceEOD, Trade


@dataclass
class PositionCalc:
    account: str
    symbol: str
    quantity: Decimal
    avg_cost: Decimal
    cost_basis: Decimal
    market_price: Decimal | None
    market_value: Decimal | None
    unrealized_pnl: Decimal | None
    realized_pnl: Decimal
    currency: str


def _to_decimal(value: Decimal) -> Decimal:
    return Decimal(value)


def _latest_prices(db: Session, symbols: Iterable[str], snapshot_date: date) -> dict[str, PriceEOD]:
    symbol_list = sorted(set(symbols))
    if not symbol_list:
        return {}

    subquery = (
        select(PriceEOD.symbol, func.max(PriceEOD.price_date).label("latest_date"))
        .where(PriceEOD.symbol.in_(symbol_list), PriceEOD.price_date <= snapshot_date)
        .group_by(PriceEOD.symbol)
        .subquery()
    )

    rows = db.scalars(
        select(PriceEOD).join(
            subquery,
            and_(
                PriceEOD.symbol == subquery.c.symbol,
                PriceEOD.price_date == subquery.c.latest_date,
            ),
        )
    ).all()

    return {row.symbol: row for row in rows}


def calculate_positions(db: Session, snapshot_date: date, account: str | None = None) -> list[PositionCalc]:
    trade_query = select(Trade).where(Trade.trade_date <= snapshot_date)
    if account:
        trade_query = trade_query.where(Trade.account == account)

    trades = db.scalars(trade_query.order_by(Trade.trade_date, Trade.id)).all()
    if not trades:
        return []

    prices = _latest_prices(db, (trade.symbol for trade in trades), snapshot_date)

    ledgers: dict[tuple[str, str], dict[str, Decimal | str]] = {}
    for trade in trades:
        key = (trade.account, trade.symbol)
        state = ledgers.setdefault(
            key,
            {
                "quantity": Decimal("0"),
                "avg_cost": Decimal("0"),
                "realized_pnl": Decimal("0"),
                "currency": trade.currency,
            },
        )

        quantity = _to_decimal(state["quantity"])
        avg_cost = _to_decimal(state["avg_cost"])
        realized_pnl = _to_decimal(state["realized_pnl"])

        trade_quantity = _to_decimal(trade.quantity)
        trade_price = _to_decimal(trade.price)
        trade_fees = _to_decimal(trade.fees)

        if trade.side == "BUY":
            total_cost = (avg_cost * quantity) + (trade_price * trade_quantity) + trade_fees
            new_quantity = quantity + trade_quantity
            new_avg_cost = total_cost / new_quantity if new_quantity > 0 else Decimal("0")
            state["quantity"] = new_quantity
            state["avg_cost"] = new_avg_cost
        else:
            matched_quantity = min(quantity, trade_quantity)
            realized_increment = (trade_price * matched_quantity - trade_fees) - (avg_cost * matched_quantity)
            new_quantity = quantity - trade_quantity
            state["quantity"] = new_quantity
            state["realized_pnl"] = realized_pnl + realized_increment
            state["avg_cost"] = Decimal("0") if new_quantity == 0 else avg_cost

    positions: list[PositionCalc] = []
    for (acct, symbol), state in sorted(ledgers.items(), key=lambda item: (item[0][0], item[0][1])):
        quantity = _to_decimal(state["quantity"])
        avg_cost = _to_decimal(state["avg_cost"])
        realized_pnl = _to_decimal(state["realized_pnl"])
        price_row = prices.get(symbol)

        market_price: Decimal | None = _to_decimal(price_row.close_price) if price_row else None
        market_value: Decimal | None = quantity * market_price if market_price is not None else None
        cost_basis = quantity * avg_cost
        unrealized_pnl: Decimal | None = market_value - cost_basis if market_value is not None else None

        positions.append(
            PositionCalc(
                account=acct,
                symbol=symbol,
                quantity=quantity,
                avg_cost=avg_cost,
                cost_basis=cost_basis,
                market_price=market_price,
                market_value=market_value,
                unrealized_pnl=unrealized_pnl,
                realized_pnl=realized_pnl,
                currency=str(state["currency"]),
            )
        )

    return positions
