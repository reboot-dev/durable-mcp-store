from store.v1.store import (
    ListProductsRequest,
    ListProductsResponse,
    GetProductRequest,
    GetProductResponse,
    SearchProductsRequest,
    SearchProductsResponse,
    AddProductRequest,
    AddProductResponse
)
from store.v1.store_rbt import ProductCatalog
from reboot.aio.auth.authorizers import allow
from reboot.aio.contexts import ReaderContext, WriterContext


class ProductCatalogServicer(ProductCatalog.Servicer):
    def authorizer(self):
        return allow()

    async def create_catalog(self, context, request) -> None:
        self.state.products = []

    async def list_products(
        self,
        context: ReaderContext,
        request: ListProductsRequest,
    ) -> ListProductsResponse:
        return ListProductsResponse(products=self.state.products)

    async def get_product(
        self,
        context: ReaderContext,
        request: GetProductRequest,
    ) -> ProductCatalog.GetProductResponse:
        for product in self.state.products:
            if request.product_id == product.id:
                return product

        raise ValueError(f"No product found with ID '{request.product_id}'")

    async def search_products(
        self,
        context: ReaderContext,
        request: SearchProductsRequest,
    ) -> SearchProductsResponse:
        query_lower = request.query.lower()
        matching_products = []

        for product in self.state.products:
            if (query_lower in product.name.lower() or
                query_lower in product.description.lower() or
                any(query_lower in category.lower() for category in product.categories)):
                matching_products.append(product)

        return SearchProductsResponse(products=matching_products)

    async def add_product(
        self,
        context: WriterContext,
        request: AddProductRequest,
    ) -> AddProductResponse:
        for product in self.state.products:
            if product.id == request.product.id:
                raise ValueError(f"Product with ID '{request.product.id}' already exists")

        self.state.products.append(request.product)

        return AddProductResponse()
