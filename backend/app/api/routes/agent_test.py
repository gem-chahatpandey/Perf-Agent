from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/agent-test")


class TestOrder(BaseModel):
    product_id: str
    quantity: int = 1


@router.get("/orders/{order_id}", name="agent_test_get_order")
async def get_order(order_id: str) -> dict:
    return {"order_id": order_id, "status": "ready"}


@router.post("/orders-created", name="agent_test_create_order")
async def create_order(order: TestOrder) -> dict:
    return {"order_id": "test-order", "product_id": order.product_id, "quantity": order.quantity}


@router.get("/payments/{payment_id}", name="agent_test_get_payment")
async def get_payment(payment_id: str) -> dict:
    return {"payment_id": payment_id, "status": "authorized"}