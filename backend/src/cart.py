import time
from store.v1.store import (
    AddItemRequest,
    GetItemsRequest,
    GetItemsResponse,
    UpdateItemQuantityRequest,
    RemoveItemRequest,
    EmptyCartRequest,
    CartItem,
    Product,
    CreateCartRequest,
)
from store.v1.store_rbt import Cart, ProductCatalog
from reboot.aio.auth.authorizers import allow
from reboot.aio.contexts import ReaderContext, WriterContext
from constants import PRODUCT_CATALOG_ID
from rbt.v1alpha1.errors_pb2 import NotFound


class CartServicer(Cart.Servicer):

    def authorizer(self):
        return allow()

    async def add_item(
        self,
        context: WriterContext,
        request: AddItemRequest,
    ) -> None:

        catalog = ProductCatalog.ref(PRODUCT_CATALOG_ID)

        try:
            product_response = await catalog.get_product(
                context,
                product_id=request.item.product_id,
            )
            product = product_response.product
        except Exception as e:
            raise Cart.AddItemAborted(
                NotFound(),
                message=f"Product not found: {request.item.product_id}"
            )

        if (not self.state.items):
            self.state.items = []

        for existing_item in self.state.items:
            if existing_item.product_id == request.item.product_id:
                existing_item.quantity += request.item.quantity
                return

        new_item = CartItem(
            product_id=request.item.product_id,
            quantity=request.item.quantity,
            name=product.name,
            price_cents=product.price_cents,
            picture=product.picture,
        )
        self.state.items.append(new_item)

    async def get_items(
        self,
        context: ReaderContext,
        request: GetItemsRequest,
    ) -> GetItemsResponse:
        return GetItemsResponse(items=self.state.items or [])

    async def update_item_quantity(
        self,
        context: WriterContext,
        request: UpdateItemQuantityRequest,
    ) -> None:
        if (not self.state.items):
            self.state.items = []

        for item in self.state.items:
            if item.product_id == request.product_id:
                item.quantity = request.quantity
                break

    async def remove_item(
        self,
        context: WriterContext,
        request: RemoveItemRequest,
    ) -> None:
        if (not self.state.items):
            return

        for i, item in enumerate(self.state.items):
            if item.product_id == request.product_id:
                del self.state.items[i]
                break

    async def empty_cart(
        self,
        context: WriterContext,
        request: EmptyCartRequest,
    ) -> None:
        self.state.items = []
