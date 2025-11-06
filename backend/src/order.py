import time
from store.v1.store import (
    GetOrdersRequest,
    GetOrdersResponse,
    AddOrderRequest,
    AddOrderResponse,
)
from store.v1.store_rbt import Orders
from reboot.aio.auth.authorizers import allow
from reboot.aio.contexts import ReaderContext, WriterContext


class OrdersServicer(Orders.Servicer):

    def authorizer(self):
        return allow()

    async def create_orders(
        self,
        context: WriterContext,
        request: Orders.CreateOrdersRequest,
    ) -> None:
        self.state.orders = []

    async def add_order(
        self,
        context: WriterContext,
        request: AddOrderRequest,
    ) -> AddOrderResponse:
        order = request.order
        if order.created_at == 0:
            order.created_at = int(time.time())

        self.state.orders.append(order)

        return AddOrderResponse()

    async def get_orders(
        self,
        context: ReaderContext,
        request: GetOrdersRequest,
    ) -> GetOrdersResponse:
        return GetOrdersResponse(orders=list(self.state.orders))
        