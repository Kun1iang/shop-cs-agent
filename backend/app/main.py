from fastapi import FastAPI
from pydantic import BaseModel

from app.api.cart import router as cart_router
from app.api.products import router as products_router

app = FastAPI(
    title="Ecom Support API",
    version="0.1.0",
)


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "shop-cs-agent-api"


@app.get(
    "/api/v1/health",
    response_model=HealthResponse,
    tags=["system"],
)
def health_check() -> HealthResponse:
    return HealthResponse()


app.include_router(products_router)
app.include_router(cart_router)

