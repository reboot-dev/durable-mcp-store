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
    name: str = Field(tag=4)
    price_cents: int = Field(tag=5)
    picture: str = Field(tag=6)

class CartState(StateModel):
    items: Optional[list[CartItem]] = Field(tag=1)

class AddItemRequest(BaseModel):
    item: CartItem = Field(tag=1)

class GetItemsRequest(BaseModel):
    pass

class GetItemsResponse(BaseModel):
    items: list[CartItem] = Field(tag=1)

class UpdateItemQuantityRequest(BaseModel):
    product_id: str = Field(tag=1)
    quantity: int = Field(tag=2)

class RemoveItemRequest(BaseModel):
    product_id: str = Field(tag=1)

class EmptyCartRequest(BaseModel):
    pass

class CreateCartRequest(BaseModel):
    pass

CartMethods = Methods(
    add_item=Writer(
        request=AddItemRequest,
        response=None,
    ),
    get_items=Reader(
        request=GetItemsRequest,
        response=GetItemsResponse,
    ),
    update_item_quantity=Writer(
        request=UpdateItemQuantityRequest,
        response=None,
    ),
    remove_item=Writer(
        request=RemoveItemRequest,
        response=None,
    ),
    empty_cart=Writer(
        request=EmptyCartRequest,
        response=None,
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
    product_catalog_ordered_map_id: str = Field(tag=1)

class ListProductsRequest(BaseModel):
    pass

class ListProductsResponse(BaseModel):
    products: list[Product] = Field(tag=1)

class GetProductRequest(BaseModel):
    product_id: str = Field(tag=1)

class GetProductResponse(BaseModel):
    product: Product = Field(tag=1)

class AddProductRequest(BaseModel):
    product: Product = Field(tag=1)

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
    add_product=Transaction(
        request=AddProductRequest,
        response=None,
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
    created_at_time: int = Field(tag=9)
    shipping_address: Address = Field(tag=10)

class OrdersState(StateModel):
    orders_ordered_map_id: Optional[str] = Field(tag=1)

class AddOrderRequest(BaseModel):
    order: Order = Field(tag=1)

class GetOrdersRequest(BaseModel):
    pass

class GetOrdersResponse(BaseModel):
    orders: list[Order] = Field(tag=1)

class CreateOrdersRequest(BaseModel):
    pass

OrdersMethods = Methods(
    add_order=Transaction(
        request=AddOrderRequest,
        response=None,
    ),
    get_orders=Reader(
        request=GetOrdersRequest,
        response=GetOrdersResponse,
    )
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
