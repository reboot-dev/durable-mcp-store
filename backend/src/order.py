import time
from store.v1.store import (
    GetOrdersRequest,
    GetOrdersResponse,
    AddOrderRequest,
    CreateOrdersRequest,
)
from store.v1.store_rbt import Orders
from reboot.aio.auth.authorizers import allow
from reboot.aio.contexts import ReaderContext, WriterContext


class OrdersServicer(Orders.Servicer):

    def authorizer(self):
        return allow()

    async def add_order(
        self,
        context: WriterContext,
        request: AddOrderRequest,
    ) -> None:
        if (not self.state.orders):
            self.state.orders = []

        self.state.orders.append(request.order)

        return None

    async def get_orders(
        self,
        context: ReaderContext,
        request: GetOrdersRequest,
    ) -> GetOrdersResponse:
        return GetOrdersResponse(orders=self.state.orders or [])
