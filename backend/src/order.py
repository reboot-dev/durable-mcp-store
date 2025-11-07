import time
from store.v1.store import (
    GetOrdersRequest, GetOrdersResponse, AddOrderRequest, AddOrderResponse,
    CreateOrdersRequest
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
        request: CreateOrdersRequest,
    ) -> None:
        self.state.orders = []

    async def add_order(
        self,
        context: WriterContext,
        request: AddOrderRequest,
    ) -> AddOrderResponse:
        self.state.orders.append(request.order)

        return AddOrderResponse()

    async def get_orders(
        self,
        context: ReaderContext,
        request: GetOrdersRequest,
    ) -> GetOrdersResponse:
        return GetOrdersResponse(orders=self.state.orders)
