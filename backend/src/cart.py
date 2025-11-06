import time
from store.v1.store import (
    AddItemRequest,
    AddItemResponse,
    GetItemsRequest,
    GetItemsResponse,
    UpdateItemQuantityRequest,
    UpdateItemQuantityResponse,
    RemoveItemRequest,
    RemoveItemResponse,
    EmptyCartRequest,
    EmptyCartResponse,
    CartItem,
)
from store.v1.store_rbt import Cart, ProductCatalog
from reboot.aio.auth.authorizers import allow
from reboot.aio.contexts import ReaderContext, WriterContext
from constants import PRODUCT_CATALOG_ID

class CartServicer(Cart.Servicer):

    def authorizer(self):
        return allow()

    async def add_item(
        self,
        context: WriterContext,
        request: AddItemRequest,
    ) -> AddItemResponse:

        try:
            product_response = await ProductCatalog.ref(PRODUCT_CATALOG_ID).get_product(
                context,
                product_id=request.item.product_id,
            )
            product = product_response.product
        except Exception as e:
            raise ValueError(
                f"Failed to fetch product {request.item.product_id}: {str(e)}"
            )

        for existing_item in self.state.items:
            if existing_item.product_id == request.item.product_id:
                existing_item.quantity += request.item.quantity
                return AddItemResponse()

        new_item = CartItem(
            product_id=request.item.product_id,
            quantity=request.item.quantity,
            added_at=int(time.time() * 1000),
            name=product.name,
            price_cents=product.price_cents,
            picture=product.picture,
        )
        self.state.items.append(new_item)

        return AddItemResponse()

    async def get_items(
        self,
        context: ReaderContext,
        request: GetItemsRequest,
    ) -> GetItemsResponse:
        return GetItemsResponse(items=self.state.items)

    async def update_item_quantity(
        self,
        context: WriterContext,
        request: UpdateItemQuantityRequest,
    ) -> UpdateItemQuantityResponse:
        for item in self.state.items:
            if item.product_id == request.product_id:
                item.quantity = request.quantity
                break

        return UpdateItemQuantityResponse()

    async def remove_item(
        self,
        context: WriterContext,
        request: RemoveItemRequest,
    ) -> RemoveItemResponse:
        new_items = [
            item for item in self.state.items
            if item.product_id != request.product_id
        ]
        del self.state.items[:]
        self.state.items.extend(new_items)

        return RemoveItemResponse()

    async def empty_cart(
        self,
        context: WriterContext,
        request: EmptyCartRequest,
    ) -> EmptyCartResponse:
        del self.state.items[:]

        return EmptyCartResponse()