from fastapi import FastAPI
from pydantic import BaseModel

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

