from fastapi import APIRouter, HTTPException, Response, status

from app import cart_service
from app.dependencies import CurrentUser, DbSession
from app.schemas import AddCartItem, CartSummary, UpdateCartItem

router = APIRouter(prefix="/api/v1/cart", tags=["cart"])


def map_cart_error(error: Exception) -> HTTPException:
    if isinstance(error, cart_service.CartItemNotFoundError):
        return HTTPException(status_code=404, detail=str(error))
    if isinstance(
        error,
        (
            cart_service.CartQuantityError,
            cart_service.VariantUnavailableError,
        ),
    ):
        return HTTPException(status_code=400, detail=str(error))
    return HTTPException(status_code=400, detail="购物车操作失败")


@router.get("", response_model=CartSummary)
def read_cart(user: CurrentUser, db: DbSession) -> CartSummary:
    cart = cart_service.get_or_create_cart(db, user.id)
    return cart_service.cart_to_summary(cart)


@router.post("/items", response_model=CartSummary)
def add_item(
    payload: AddCartItem,
    user: CurrentUser,
    db: DbSession,
) -> CartSummary:
    try:
        cart = cart_service.add_cart_item(
            db,
            user.id,
            payload.variant_id,
            payload.quantity,
        )
    except Exception as error:
        raise map_cart_error(error) from error
    return cart_service.cart_to_summary(cart)


@router.patch("/items/{item_id}", response_model=CartSummary)
def update_item(
    item_id: int,
    payload: UpdateCartItem,
    user: CurrentUser,
    db: DbSession,
) -> CartSummary:
    try:
        cart = cart_service.update_cart_item(
            db,
            user.id,
            item_id,
            payload.quantity,
        )
    except Exception as error:
        raise map_cart_error(error) from error
    return cart_service.cart_to_summary(cart)


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(
    item_id: int,
    user: CurrentUser,
    db: DbSession,
) -> Response:
    try:
        cart_service.delete_cart_item(db, user.id, item_id)
    except Exception as error:
        raise map_cart_error(error) from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)

