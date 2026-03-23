import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.models.trade import Trade
from app.schemas.trade import TradeCreate, TradeRead, TradeUpdate

router = APIRouter()


@router.get("", response_model=list[TradeRead])
async def list_trades(db: AsyncSession = Depends(get_db_session)) -> list[Trade]:
    result = await db.execute(select(Trade).order_by(Trade.opened_at.desc()))
    return list(result.scalars().all())


@router.get("/{trade_id}", response_model=TradeRead)
async def get_trade(trade_id: uuid.UUID, db: AsyncSession = Depends(get_db_session)) -> Trade:
    trade = await db.get(Trade, trade_id)
    if trade is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trade not found")
    return trade


@router.post("", response_model=TradeRead, status_code=status.HTTP_201_CREATED)
async def create_trade(payload: TradeCreate, db: AsyncSession = Depends(get_db_session)) -> Trade:
    trade = Trade(**payload.model_dump())
    db.add(trade)
    await db.commit()
    await db.refresh(trade)
    return trade


@router.patch("/{trade_id}", response_model=TradeRead)
async def update_trade(
    trade_id: uuid.UUID,
    payload: TradeUpdate,
    db: AsyncSession = Depends(get_db_session),
) -> Trade:
    trade = await db.get(Trade, trade_id)
    if trade is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trade not found")

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(trade, key, value)

    await db.commit()
    await db.refresh(trade)
    return trade


@router.delete("/{trade_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_trade(trade_id: uuid.UUID, db: AsyncSession = Depends(get_db_session)) -> None:
    trade = await db.get(Trade, trade_id)
    if trade is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trade not found")

    await db.delete(trade)
    await db.commit()
