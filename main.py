import asyncio
import os
import random
import time
import urllib.parse
from mcp_ui_server import create_ui_resource
from mcp_ui_server.core import UIResource
from reboot.aio.external import InitializeContext
from reboot.aio.workflows import at_least_once, at_most_once
from reboot.mcp.server import DurableMCP, DurableContext
from backend.src.cart import CartServicer
from backend.src.product import ProductCatalogServicer
from backend.src.order import OrdersServicer
from store.v1.store import Product, CartItem, Order, Address
from store.v1.store_rbt import ProductCatalog, Cart, Orders
from constants import PRODUCT_CATALOG_ID, USER_ID
from rbt.v1alpha1.errors_pb2 import Aborted
from reboot.std.collections.ordered_map.v1 import ordered_map

mcp = DurableMCP(path="/mcp")


@mcp.tool()
def show_products(
    search_query: str,
    context: DurableContext,
) -> list[UIResource]:
    """Display products matching the search query in an interactive UI.

    Args:
        search_query: The search term to filter products (e.g., 'shirts', 
        'pants', 'blue').
    """
    if search_query == "all":
        search_query = ""

    encoded_query = urllib.parse.quote(search_query or "")

    iframe_url = "http://localhost:3000/products"
    if search_query:
        iframe_url = f"http://localhost:3000/products?query={encoded_query}"

    ui_resource = create_ui_resource(
        {
            "uri":
                f"ui://products/search/{encoded_query}"
                if search_query else "ui://products/all",
            "content": {
                "type": "externalUrl",
                "iframeUrl": iframe_url
            },
            "encoding":
                "text"
        }
    )
    return [ui_resource]


@mcp.tool()
def show_cart(context: DurableContext) -> list[UIResource]:
    """Display the shopping cart in an interactive UI."""
    iframe_url = f"http://localhost:3000/cart?cart_id={USER_ID}"

    ui_resource = create_ui_resource(
        {
            "uri": f"ui://cart",
            "content": {
                "type": "externalUrl",
                "iframeUrl": iframe_url
            },
            "encoding": "text"
        }
    )
    return [ui_resource]


@mcp.tool()
def show_orders(context: DurableContext) -> list[UIResource]:
    """Display past orders in an interactive UI."""
    iframe_url = f"http://localhost:3000/orders?orders_id={USER_ID}"

    ui_resource = create_ui_resource(
        {
            "uri": f"ui://orders",
            "content": {
                "type": "externalUrl",
                "iframeUrl": iframe_url
            },
            "encoding": "text"
        }
    )
    return [ui_resource]


@mcp.tool()
async def add_item_to_cart(
    product_id: str, quantity: int, context: DurableContext
) -> list[UIResource]:
    """Add an item to the shopping cart.

    Args:
        product_id: The ID of the product to add.
        quantity: The quantity to add (default: 1).
    """
    cart_id = USER_ID

    get_product_response = await ProductCatalog.ref(
        PRODUCT_CATALOG_ID
    ).get_product(
        context,
        product_id=product_id,
    )
    product = get_product_response.product

    await Cart.ref(cart_id).add_item(
        context,
        item=CartItem(
            product_id=product_id,
            quantity=quantity,
            name=product.name,
            price_cents=product.price_cents,
            picture=product.picture,
        ),
    )

    iframe_url = f"http://localhost:3000/cart?cart_id={cart_id}"

    ui_resource = create_ui_resource(
        {
            "uri": f"ui://cart",
            "content": {
                "type": "externalUrl",
                "iframeUrl": iframe_url
            },
            "encoding": "text"
        }
    )
    return [ui_resource]


# Mock functions for checkout workflow.
async def get_shipping_quote(items: list, address: dict) -> dict:
    """Mock function to get shipping quote."""
    # In real implementation, this would call a shipping API.
    total_weight = len(items) * 2  # Mock weight calculation.
    base_cost = 500  # $5.00 base.
    weight_cost = total_weight * 50  # $0.50 per pound.
    total_cost = base_cost + weight_cost

    return {
        "cost_cents": total_cost,
        "carrier": "Mock Shipping Co.",
        "estimated_days": random.randint(3, 7),
    }


async def charge_credit_card(card_info: dict, amount_cents: int) -> dict:
    """Mock function to charge credit card (non-idempotent)."""
    # In real implementation, this would call a payment processor.
    return {
        "transaction_id": f"txn_{random.randint(100000, 999999)}",
        "last_four": card_info.get("number", "0000")[-4:],
        "amount_cents": amount_cents,
    }


async def ship_order(items: list, address: dict, carrier: str) -> dict:
    """Mock function to ship order (non-idempotent)."""
    # In real implementation, this would call a shipping API.
    return {
        "tracking_number": f"TRACK{random.randint(1000000000, 9999999999)}",
        "carrier": carrier,
        "status": "shipped",
    }


@mcp.tool()
async def checkout(
    card_number: str,
    card_cvv: int,
    card_expiration_month: int,
    card_expiration_year: int,
    shipping_street_address: str,
    shipping_city: str,
    shipping_state: str,
    shipping_country: str,
    shipping_zip_code: str,
    context: DurableContext,
) -> list[UIResource]:
    """Complete the checkout process for items in the cart.

    Args:
        card_number: Credit card number
        card_cvv: Credit card CVV
        card_expiration_month: Credit card expiration month
        card_expiration_year: Credit card expiration year
        shipping_street_address: Shipping street address
        shipping_city: Shipping city
        shipping_state: Shipping state
        shipping_country: Shipping country
        shipping_zip_code: Shipping zip code
    """
    cart_id = USER_ID
    orders_id = USER_ID

    cart_response = await Cart.ref(cart_id).get_items(context)
    items = list(cart_response.items)

    if len(items) == 0:
        raise Cart.GetItemsAborted(Aborted(), message="Cart is empty.")

    subtotal_cents = sum(item.price_cents * item.quantity for item in items)

    address = {
        "street_address": shipping_street_address,
        "city": shipping_city,
        "state": shipping_state,
        "country": shipping_country,
        "zip_code": shipping_zip_code,
    }

    async def get_quote():
        return await get_shipping_quote(items, address)

    shipping_quote = await at_least_once(
        "Get shipping quote",
        context,
        get_quote,
        type=dict,
    )

    total_cents = subtotal_cents + shipping_quote["cost_cents"]

    async def charge_card() -> dict:
        return await charge_credit_card(
            {
                "number": card_number,
                "cvv": card_cvv,
                "expiration_month": card_expiration_month,
                "expiration_year": card_expiration_year,
            },
            total_cents,
        )

    # Simulate failure for testing retry logic.
    # To simulate failure set the environment variable FAIL_CHECKOUT=anything.
    if os.environ.get("FAIL_CHECKOUT"):
        await asyncio.Event().wait()

    charge_result = await at_least_once(
        "Charge credit card",
        context,
        charge_card,
        type=dict,
    )

    async def ship() -> dict:
        return await ship_order(items, address, shipping_quote["carrier"])

    shipping_result = await at_least_once(
        "Ship order",
        context,
        ship,
        type=dict,
    )

    async def generate_order_id() -> str:
        return f"order_{random.randint(100000, 999999)}"

    order_id = await at_least_once(
        "Generate order ID",
        context,
        generate_order_id,
        type=str,
    )

    order = Order(
        order_id=order_id,
        items=items,
        transaction_id=charge_result["transaction_id"],
        subtotal_cents=subtotal_cents,
        shipping_cost_cents=shipping_quote["cost_cents"],
        total_cents=total_cents,
        tracking_number=shipping_result["tracking_number"],
        carrier=shipping_result["carrier"],
        created_at_time=int(time.time() * 1000),
        shipping_address=Address(
            street_address=shipping_street_address,
            city=shipping_city,
            state=shipping_state,
            country=shipping_country,
            zip_code=shipping_zip_code,
        ),
    )

    await Orders.ref(orders_id).add_order(context, order=order)

    await Cart.ref(cart_id).empty_cart(context)

    encoded_order = urllib.parse.quote(
        f"{order_id}|{charge_result}|{subtotal_cents}|"
        f"{shipping_quote['cost_cents']}|{total_cents}|{shipping_result}"
    )

    iframe_url = f"http://localhost:3000/order?data={encoded_order}"

    ui_resource = create_ui_resource(
        {
            "uri": f"ui://order/{order_id}",
            "content": {
                "type": "externalUrl",
                "iframeUrl": iframe_url
            },
            "encoding": "text"
        }
    )

    return [ui_resource]


async def initialize(context: InitializeContext):
    """Initialize the product catalog with mock products."""

    catalog, _ = await ProductCatalog.create_catalog(
        context,
        PRODUCT_CATALOG_ID,
    )

    products = [
        Product(
            id="shirt-001",
            name="Classic Blue Shirt",
            description="A comfortable cotton shirt in classic blue",
            picture="https://pngimg.com/uploads/tshirt/tshirt_PNG5437.png",
            price_cents=2999,
            categories=["shirts", "men", "casual"],
            stock_quantity=50,
        ),
        Product(
            id="shirt-002",
            name="White Dress Shirt",
            description="Elegant white dress shirt for formal occasions",
            picture="https://pngimg.com/uploads/tshirt/tshirt_PNG5447.png",
            price_cents=3999,
            categories=["shirts", "men", "formal"],
            stock_quantity=30,
        ),
        Product(
            id="shirt-003",
            name="Black Polo Shirt",
            description="Sporty black polo shirt",
            picture="https://pngimg.com/uploads/tshirt/tshirt_PNG5427.png",
            price_cents=3499,
            categories=["shirts", "men", "sports"],
            stock_quantity=25,
        ),
        Product(
            id="shirt-004",
            name="Red Flannel Shirt",
            description="Cozy red flannel for casual wear",
            picture="https://pngimg.com/uploads/tshirt/tshirt_PNG5437.png",
            price_cents=4599,
            categories=["shirts", "men", "casual"],
            stock_quantity=20,
        ),
        Product(
            id="shirt-005",
            name="Striped Button-Down",
            description="Navy striped button-down shirt",
            picture="https://pngimg.com/uploads/tshirt/tshirt_PNG5454.png",
            price_cents=3899,
            categories=["shirts", "men", "business"],
            stock_quantity=15,
        ),
        Product(
            id="pants-001",
            name="Denim Jeans",
            description="Classic blue denim jeans",
            picture="https://pngimg.com/uploads/jeans/jeans_PNG5763.png",
            price_cents=4999,
            categories=["pants", "men", "casual"],
            stock_quantity=40,
        ),
        Product(
            id="pants-002",
            name="Khaki Chinos",
            description="Versatile khaki chinos",
            picture="https://pngimg.com/uploads/jeans/jeans_PNG5763.png",
            price_cents=4499,
            categories=["pants", "men", "casual"],
            stock_quantity=35,
        ),
        Product(
            id="pants-003",
            name="Black Dress Pants",
            description="Formal black dress pants",
            picture="https://pngimg.com/uploads/jeans/jeans_PNG5763.png",
            price_cents=5999,
            categories=["pants", "men", "formal"],
            stock_quantity=25,
        ),
        Product(
            id="pants-004",
            name="Gray Joggers",
            description="Comfortable gray joggers",
            picture="https://pngimg.com/uploads/jeans/jeans_PNG5763.png",
            price_cents=4299,
            categories=["pants", "men", "sports"],
            stock_quantity=30,
        ),
        Product(
            id="shoes-001",
            name="White Sneakers",
            description="Classic white leather sneakers",
            picture=
            "https://pngimg.com/uploads/men_shoes/men_shoes_PNG7476.png",
            price_cents=7999,
            categories=["shoes", "casual", "sports"],
            stock_quantity=45,
        ),
        Product(
            id="shoes-002",
            name="Black Running Shoes",
            description="High-performance running shoes",
            picture=
            "https://pngimg.com/uploads/men_shoes/men_shoes_PNG7476.png",
            price_cents=8999,
            categories=["shoes", "sports", "athletic"],
            stock_quantity=5,
        ),
        Product(
            id="shoes-003",
            name="Brown Leather Boots",
            description="Rugged brown leather boots",
            picture=
            "https://pngimg.com/uploads/men_shoes/men_shoes_PNG7476.png",
            price_cents=12000,
            categories=["shoes", "boots", "casual"],
            stock_quantity=18,
        ),
        Product(
            id="shoes-004",
            name="Blue Canvas Shoes",
            description="Lightweight blue canvas shoes",
            picture=
            "https://pngimg.com/uploads/men_shoes/men_shoes_PNG7476.png",
            price_cents=5500,
            categories=["shoes", "casual", "summer"],
            stock_quantity=28,
        ),
        Product(
            id="jackets-001",
            name="Black Leather Jacket",
            description="Classic black leather jacket",
            picture="https://pngimg.com/uploads/jacket/jacket_PNG8047.png",
            price_cents=14999,
            categories=["jackets", "outerwear", "casual"],
            stock_quantity=12,
        ),
        Product(
            id="jackets-002",
            name="Navy Windbreaker",
            description="Lightweight navy windbreaker",
            picture="https://pngimg.com/uploads/jacket/jacket_PNG8036.png",
            price_cents=6999,
            categories=["jackets", "outerwear", "sports"],
            stock_quantity=22,
        ),
        Product(
            id="jackets-003",
            name="Gray Hoodie",
            description="Cozy gray hooded sweatshirt",
            picture="https://pngimg.com/uploads/jacket/jacket_PNG8039.png",
            price_cents=5499,
            categories=["jackets", "hoodies", "casual"],
            stock_quantity=35,
        ),
        Product(
            id="jackets-004",
            name="Denim Jacket",
            description="Classic blue denim jacket",
            picture="https://pngimg.com/uploads/jacket/jacket_PNG8049.png",
            price_cents=7999,
            categories=["jackets", "denim", "casual"],
            stock_quantity=18,
        ),
        Product(
            id="accessories-001",
            name="Black Leather Belt",
            description="Premium black leather belt",
            picture="https://www.hnwilliams.com/wp-content/uploads/2024/01/BLACK_305.jpg",
            price_cents=3500,
            categories=["accessories", "belts", "leather"],
            stock_quantity=40,
        ),
        Product(
            id="accessories-002",
            name="Blue Baseball Cap",
            description="Casual blue baseball cap",
            picture="https://pngimg.com/uploads/cap/cap_PNG5674.png",
            price_cents=2500,
            categories=["accessories", "hats", "casual"],
            stock_quantity=50,
        ),
        Product(
            id="accessories-003",
            name="Sunglasses",
            description="Stylish black sunglasses",
            picture=
            "https://pngimg.com/uploads/sunglasses/sunglasses_PNG142.png",
            price_cents=4599,
            categories=["accessories", "sunglasses", "summer"],
            stock_quantity=8,
        ),
        Product(
            id="accessories-004",
            name="Wool Scarf",
            description="Warm gray wool scarf",
            picture="https://pngimg.com/uploads/scarf/scarf_PNG27.png",
            price_cents=3200,
            categories=["accessories", "scarves", "winter"],
            stock_quantity=20,
        ),
        Product(
            id="accessories-005",
            name="Leather Watch",
            description="Brown leather strap watch",
            picture="https://www.nixon.com/cdn/shop/files/A105-2001-view1.png?v=1718724157",
            price_cents=9500,
            categories=["accessories", "watches", "formal"],
            stock_quantity=15,
        ),
        Product(
            id="bags-001",
            name="Black Backpack",
            description="Spacious black backpack",
            picture="https://us.oneill.com/cdn/shop/products/SU3195000_BLK_8.jpg?v=1675818358",
            price_cents=6500,
            categories=["bags", "backpacks", "casual"],
            stock_quantity=30,
        ),
        Product(
            id="bags-002",
            name="Brown Messenger Bag",
            description="Vintage brown messenger bag",
            picture="https://www.rustictown.com/cdn/shop/products/Rustictown_LeatherMessengerBagforMen_LeatherSatchelBag_LeatherBriefcase_1074dd7e-52c0-4c38-8f9b-50c833de40e4.webp?v=1681986221&width=2000",
            price_cents=8500,
            categories=["bags", "messenger", "business"],
            stock_quantity=12,
        ),
        Product(
            id="bags-003",
            name="Gym Duffel Bag",
            description="Large gym duffel bag",
            picture="https://totebagfactory.com/cdn/shop/products/quality-black-gym-bag.png?v=1600469072&width=1214",
            price_cents=4899,
            categories=["bags", "sports", "gym"],
            stock_quantity=25,
        ),
    ]

    for product in products:
        await catalog.idempotently(f"add-product-{product.id}").add_product(
            context,
            product=product,
        )


async def main():
    await mcp.application(
        servicers=[
            CartServicer,
            ProductCatalogServicer,
            OrdersServicer,
        ] + ordered_map.servicers(),
        initialize=initialize,
    ).run()


if __name__ == '__main__':
    asyncio.run(main())
