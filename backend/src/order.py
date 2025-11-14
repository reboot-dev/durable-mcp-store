import time
from store.v1.store import (
    GetOrdersRequest,
    GetOrdersResponse,
    AddOrderRequest,
    CreateOrdersRequest,
    Order,
)
from store.v1.store_rbt import Orders
from reboot.aio.auth.authorizers import allow
from reboot.aio.contexts import ReaderContext, WriterContext
from reboot.std.collections.ordered_map.v1.ordered_map import OrderedMap
from reboot.protobuf import from_model, as_model
from constants import ORDERS_ID


class OrdersServicer(Orders.Servicer):

    def authorizer(self):
        return allow()

    async def add_order(
        self,
        context: WriterContext,
        request: AddOrderRequest,
    ) -> None:
        await self.orders.insert(
            context,
            key=request.order.order_id,
            value=from_model(request.order),
        )

    async def get_orders(
        self,
        context: ReaderContext,
        request: GetOrdersRequest,
    ) -> GetOrdersResponse:
        # TODO: Add pagination.
        orders_range = await self.orders.range(context, limit=300)

        return GetOrdersResponse(
            orders=[
                as_model(order.value, model_type=Order)
                for order in orders_range.entries
            ]
        )

    @property
    def orders(self) -> OrderedMap.WeakReference:
        """Helper to get reference to `OrderedMap` for orders."""
        return OrderedMap.ref(ORDERS_ID)
