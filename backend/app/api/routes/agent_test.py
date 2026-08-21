from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/agent-test")


class TestOrder(BaseModel):
    product_id: str
    quantity: int = Field(default=1, ge=1)


class PaymentRequest(BaseModel):
    payment_id: str
    order_id: str
    amount: float = Field(gt=0)


orders = {
    "order-1": {"product_id": "product-1", "quantity": 1, "payment_id": "payment-1"},
}
payments = {
    "payment-1": {"status": "authorized", "transaction_id": "txn-1", "payment_method": "card"},
}
inventory = {
    "product-1": {"available_quantity": 10, "reserved_quantity": 0},
}


async def fetch_order(order_id: str) -> dict:
    if order_id not in orders:
        raise HTTPException(404, "Order not found")
    return orders[order_id]


async def fetch_payment(payment_id: str) -> dict:
    if payment_id not in payments:
        raise HTTPException(404, "Payment not found")
    return payments[payment_id]


async def fetch_inventory(product_id: str) -> dict:
    return inventory.setdefault(product_id, {"available_quantity": 10, "reserved_quantity": 0})


@router.get("/orders/{order_id}", name="agent_test_get_order")
async def get_order(order_id: str) -> dict:
    order = await fetch_order(order_id)
    payment = await get_payment(order["payment_id"])

    return {
        "order_id": order_id,
        "product_id": order["product_id"],
        "quantity": order["quantity"],
        "payment_status": payment["status"],
        "status": "ready",
    }


@router.post("/orders", name="agent_test_create_order")
async def create_order(order: TestOrder) -> dict:
    await reserve_inventory(
        product_id=order.product_id,
        quantity=order.quantity,
    )
    order_id = f"order-{len(orders) + 1}"
    orders[order_id] = {"product_id": order.product_id, "quantity": order.quantity, "payment_id": ""}

    return {
        "order_id": order_id,
        "product_id": order.product_id,
        "quantity": order.quantity,
        "status": "created",
    }

@router.get("/payments/{payment_id}", name="agent_test_get_payment")
async def get_payment(payment_id: str) -> dict:
    payment = await fetch_payment(payment_id)

    return {
        "payment_id": payment_id,
        "status": payment["status"],
        "transaction_id": payment["transaction_id"],
        "payment_method": payment.get("payment_method"),
        "is_successful": payment["status"] == "authorized",
    }

@router.post("/payments", name="agent_test_create_payment")
async def create_payment(payment: PaymentRequest) -> dict:
    order = await get_order(payment.order_id)

    transaction_id = f"txn-{payment.payment_id}"
    payments[payment.payment_id] = {"status": "authorized", "transaction_id": transaction_id, "payment_method": "card"}

    return {
        "payment_id": payment.payment_id,
        "order_id": payment.order_id,
        "transaction_id": transaction_id,
        "status": "authorized",
    }


@router.get("/inventory/{product_id}", name="agent_test_get_inventory")
async def get_inventory(product_id: str) -> dict:
    inventory = await fetch_inventory(product_id)

    return {
        "product_id": product_id,
        "available_quantity": inventory["available_quantity"],
        "reserved_quantity": inventory["reserved_quantity"],
    }

@router.post("/inventory/reserve", name="agent_test_reserve_inventory")
async def reserve_inventory(
    product_id: str,
    quantity: int
) -> dict:
    inventory = await get_inventory(product_id)

    if quantity <= 0:
        return {
            "product_id": product_id,
            "status": "invalid_quantity"
        }

    if inventory["available_quantity"] < quantity:
        return {
            "product_id": product_id,
            "status": "insufficient_inventory",
            "available_quantity": inventory["available_quantity"]
        }

    return {
        "product_id": product_id,
        "reserved_quantity": quantity,
        "remaining_quantity": inventory["available_quantity"] - quantity,
        "status": "reserved",
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
        "status": "cancelled",
    }


@router.post("/inventory/release", name="agent_test_release_inventory")
async def release_inventory(
    product_id: str,
    quantity: int
) -> dict:
    stock = await fetch_inventory(product_id)
    stock["available_quantity"] += quantity
    stock["reserved_quantity"] = max(0, stock["reserved_quantity"] - quantity)
    return {
        "product_id": product_id,
        "released_quantity": quantity,
        "status": "released",
    }