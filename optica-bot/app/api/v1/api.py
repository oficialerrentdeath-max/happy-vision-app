from app.core.config import APIRouter
from app.api.v1.endpoints import orders, payments

api_router = APIRouter()
api_router.include_router(orders.router, prefix="", tags=["orders"])
api_router.include_router(payments.router, prefix="", tags=["payments"])
