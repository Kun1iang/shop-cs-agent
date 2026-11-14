from typing import Annotated

from fastapi import APIRouter, Header, HTTPException

from app import order_service
from app.dependencies import CurrentUser, DbSession
from app.schemas import OrderSummary

router = APIRouter(prefix="/api/v1/orders", tags=["orders"])


def map_order_error(error: Exception) -> HTTPException:
    if isinstance(error, order_service.EmptyCartError):
        return HTTPException(status_code=400, detail=str(error))
    if isinstance(error, order_service.OrderStockError):
        return HTTPException(status_code=409, detail=str(error))
    if isinstance(error, order_service.OrderNotFoundError):
        return HTTPException(status_code=404, detail=str(error))
    return HTTPException(status_code=400, detail="订单操作失败")


@router.post("/checkout", response_model=OrderSummary)
def checkout(
    user: CurrentUser,
    db: DbSession,
    idempotency_key: Annotated[
        str,
        Header(alias="Idempotency-Key", min_length=8),
    ],
) -> OrderSummary:
    try:
        return order_service.checkout(db, user.id, idempotency_key)
    except Exception as error:
        raise map_order_error(error) from error


@router.get("", response_model=list[OrderSummary])
def read_orders(user: CurrentUser, db: DbSession) -> list[OrderSummary]:
    return order_service.list_orders(db, user.id)


@router.get("/{order_no}", response_model=OrderSummary)
def read_order(
    order_no: str,
    user: CurrentUser,
    db: DbSession,
) -> OrderSummary:
    try:
        return order_service.get_order(db, user.id, order_no)
    except Exception as error:
        raise map_order_error(error) from error

