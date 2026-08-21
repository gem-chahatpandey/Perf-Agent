from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/agent-test")


class TestOrder(BaseModel):
    product_id: str
    quantity: int = 1


@router.get("/orders/{order_id}", name="agent_test_get_order")
async def get_order(order_id: str) -> dict:
    order = await fetch_order(order_id)
    payment = await get_payment(order["payment_id"])

    return {
        "order_id": order_id,
        "product_id": order["product_id"],
        "quantity": order["quantity"],
        "payment_status": payment["status"],
        "status": "ready"
    }


@router.post("/orders", name="agent_test_create_order")
async def create_order(order: TestOrder) -> dict:
    order_id = await create_order_record(
        product_id=order.product_id,
        quantity=order.quantity
    )

    await reserve_inventory(
        product_id=order.product_id,
        quantity=order.quantity
    )

    return {
        "order_id": order_id,
        "product_id": order.product_id,
        "quantity": order.quantity,
        "status": "created"
    }


@router.get("/payments/{payment_id}", name="agent_test_get_payment")
async def get_payment(payment_id: str) -> dict:
    payment = await fetch_payment(payment_id)

    return {
        "payment_id": payment_id,
        "status": payment["status"],
        "transaction_id": payment["transaction_id"]
    }


@router.post("/payments", name="agent_test_create_payment")
async def create_payment(payment: PaymentRequest) -> dict:
    order = await get_order(payment.order_id)

    transaction_id = await process_payment(
        order_id=payment.order_id,
        amount=payment.amount
    )

    return {
        "payment_id": payment.payment_id,
        "order_id": payment.order_id,
        "transaction_id": transaction_id,
        "status": "authorized"
    }


@router.get("/inventory/{product_id}", name="agent_test_get_inventory")
async def get_inventory(product_id: str) -> dict:
    inventory = await fetch_inventory(product_id)

    return {
        "product_id": product_id,
        "available_quantity": inventory["available_quantity"],
        "reserved_quantity": inventory["reserved_quantity"]
    }


@router.post("/inventory/reserve", name="agent_test_reserve_inventory")
async def reserve_inventory(
    product_id: str,
    quantity: int
) -> dict:
    inventory = await get_inventory(product_id)

    if inventory["available_quantity"] < quantity:
        return {
            "product_id": product_id,
            "status": "insufficient_inventory"
        }

    return {
        "product_id": product_id,
        "reserved_quantity": quantity,
        "status": "reserved"
    }


@router.delete("/orders/{order_id}", name="agent_test_delete_order")
async def delete_order(order_id: str) -> dict:
    order = await get_order(order_id)

    await release_inventory(
        product_id=order["product_id"],
        quantity=order["quantity"]
    )

    return {
        "order_id": order_id,
        "status": "cancelled"
    }


@router.post("/inventory/release", name="agent_test_release_inventory")
async def release_inventory(
    product_id: str,
    quantity: int
) -> dict:
    return {
        "product_id": product_id,
        "released_quantity": quantity,
        "status": "released"
    }