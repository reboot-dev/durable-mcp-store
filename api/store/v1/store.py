from pydantic import BaseModel
from typing import Optional

from reboot.api import (
    API,
    Field,
    Methods,
    Reader,
    StateModel,
    Transaction,
    Type,
    Writer,
)

########################################################################
# Cart
########################################################################

class CartItem(BaseModel):
    product_id: str = Field(tag=1)
    quantity: int = Field(tag=2)
    added_at: int = Field(tag=3)
    name: str = Field(tag=4)
    price_cents: int = Field(tag=5)
    picture: str = Field(tag=6)

class CartState(StateModel):
    items: Optional[list[CartItem]] = Field(tag=1)

class AddItemRequest(BaseModel):
    item: CartItem = Field(tag=1)

class AddItemResponse(BaseModel):
    pass

class GetItemsRequest(BaseModel):
    pass

class GetItemsResponse(BaseModel):
    items: list[CartItem] = Field(tag=1)

class UpdateItemQuantityRequest(BaseModel):
    product_id: str = Field(tag=1)
    quantity: int = Field(tag=2)

class UpdateItemQuantityResponse(BaseModel):
    pass

class RemoveItemRequest(BaseModel):
    product_id: str = Field(tag=1)

class RemoveItemResponse(BaseModel):
    pass

class EmptyCartRequest(BaseModel):
    pass

class EmptyCartResponse(BaseModel):
    pass

class CreateCartRequest(BaseModel):
    pass

CartMethods = Methods(
    add_item=Writer(
        request=AddItemRequest,
        response=AddItemResponse,
    ),
    get_items=Reader(
        request=GetItemsRequest,
        response=GetItemsResponse,
    ),
    update_item_quantity=Writer(
        request=UpdateItemQuantityRequest,
        response=UpdateItemQuantityResponse,
    ),
    remove_item=Writer(
        request=RemoveItemRequest,
        response=RemoveItemResponse,
    ),
    empty_cart=Writer(
        request=EmptyCartRequest,
        response=EmptyCartResponse,
    ),
    create_cart=Writer(
        request=CreateCartRequest,
        response=None,
        factory=True,
    ),
)

########################################################################
# ProductCatalog
########################################################################

class Product(BaseModel):
    id: str = Field(tag=1)
    name: str = Field(tag=2)
    description: str = Field(tag=3)
    picture: str = Field(tag=4)
    price_cents: int = Field(tag=5)
    categories: list[str] = Field(tag=6)
    stock_quantity: int = Field(tag=7)

class ProductCatalogState(StateModel):
    products: list[Product] = Field(tag=1)

class ListProductsRequest(BaseModel):
    pass

class ListProductsResponse(BaseModel):
    products: list[Product] = Field(tag=1)

class GetProductRequest(BaseModel):
    product_id: str = Field(tag=1)

class GetProductResponse(BaseModel):
    product: Product = Field(tag=1)

class SearchProductsRequest(BaseModel):
    query: str = Field(tag=1)

class SearchProductsResponse(BaseModel):
    products: list[Product] = Field(tag=1)

class AddProductRequest(BaseModel):
    product: Product = Field(tag=1)

class AddProductResponse(BaseModel):
    pass

class CreateCatalogRequest(BaseModel):
    pass

ProductCatalogMethods = Methods(
    list_products=Reader(
        request=ListProductsRequest,
        response=ListProductsResponse,
    ),
    get_product=Reader(
        request=GetProductRequest,
        response=GetProductResponse,
    ),
    search_products=Reader(
        request=SearchProductsRequest,
        response=SearchProductsResponse,
    ),
    add_product=Writer(
        request=AddProductRequest,
        response=AddProductResponse,
    ),
    create_catalog=Writer(
        request=CreateCatalogRequest,
        response=None,
        factory=True,
    )
)

########################################################################
# Orders
########################################################################

class Address(BaseModel):
    street_address: str = Field(tag=1)
    city: str = Field(tag=2)
    state: str = Field(tag=3)
    country: str = Field(tag=4)
    zip_code: str = Field(tag=5)

class Order(BaseModel):
    order_id: str = Field(tag=1)
    items: list[CartItem] = Field(tag=2)
    transaction_id: str = Field(tag=3)
    subtotal_cents: int = Field(tag=4)
    shipping_cost_cents: int = Field(tag=5)
    total_cents: int = Field(tag=6)
    tracking_number: str = Field(tag=7)
    carrier: str = Field(tag=8)
    created_at: int = Field(tag=9)
    shipping_address: Address = Field(tag=10)

class OrdersState(StateModel):
    orders: Optional[list[Order]] = Field(tag=1)

class AddOrderRequest(BaseModel):
    order: Order = Field(tag=1)

class AddOrderResponse(BaseModel):
    pass

class GetOrdersRequest(BaseModel):
    pass

class GetOrdersResponse(BaseModel):
    orders: list[Order] = Field(tag=1)

class CreateOrdersRequest(BaseModel):
    pass

OrdersMethods = Methods(
    add_order=Writer(
        request=AddOrderRequest,
        response=AddOrderResponse,
    ),
    get_orders=Reader(
        request=GetOrdersRequest,
        response=GetOrdersResponse,
    ),
    create_orders=Writer(
        request=CreateOrdersRequest,
        response=None,
        factory=True,
    ),
)

########################################################################
# API
########################################################################

api = API(
    Cart=Type(
        state=CartState,
        methods=CartMethods,
    ),
    ProductCatalog=Type(
        state=ProductCatalogState,
        methods=ProductCatalogMethods,
    ),
    Orders=Type(
        state=OrdersState,
        methods=OrdersMethods,
    ),
)
