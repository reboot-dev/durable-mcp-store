from store.v1.store import (
    ListProductsRequest,
    ListProductsResponse,
    GetProductRequest,
    GetProductResponse,
    AddProductRequest,
    CreateCatalogRequest,
    Product,
)
from store.v1.store_rbt import ProductCatalog
from reboot.aio.auth.authorizers import allow
from reboot.aio.contexts import ReaderContext, WriterContext, TransactionContext
from rbt.v1alpha1.errors_pb2 import NotFound
from reboot.std.collections.ordered_map.v1.ordered_map import OrderedMap
from reboot.protobuf import from_model, as_model
from constants import PRODUCT_CATALOG_ID

class ProductCatalogServicer(ProductCatalog.Servicer):

    def authorizer(self):
        return allow()

    async def list_products(
        self,
        context: ReaderContext,
        request: ListProductsRequest,
    ) -> ListProductsResponse:
        # TODO: Add pagination.
        products_range = await self.catalog.range(context, limit=300)

        products = [
            as_model(product.value, model_type=Product)
            for product in products_range.entries
        ]

        return ListProductsResponse(products=products)

    async def get_product(
        self,
        context: ReaderContext,
        request: GetProductRequest,
    ) -> GetProductResponse:
        response = await self.catalog.search(context, key=request.product_id)

        if response.found:
            product = as_model(response.value, model_type=Product)
            return GetProductResponse(product=product)

        raise ProductCatalog.GetProductAborted(
            NotFound(), message=f"Product not found: {request.product_id}"
        )

    async def add_product(
        self,
        context: TransactionContext,
        request: AddProductRequest,
    ) -> None:
        await self.catalog.insert(
            context,
            key=request.product.id,
            value=from_model(request.product),
        )

    @property
    def catalog(self) -> OrderedMap.WeakReference:
        """Helper to get reference to `OrderedMap` for catalog."""
        return OrderedMap.ref(PRODUCT_CATALOG_ID)
