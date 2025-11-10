import { useSearchParams } from "react-router-dom";
import { useProductCatalog } from "../../api/store/v1/store_rbt_react";
import { PRODUCT_CATALOG_ID } from "../../constants";

const Products = () => {
  const [searchParams] = useSearchParams();
  const query = searchParams.get("query") || undefined;

  const { useListProducts } = useProductCatalog({ id: PRODUCT_CATALOG_ID });
  const { response } = useListProducts();

  if (response === undefined) return <>Loading...</>;
  const products = response.products?.elements ?? [];

  const filteredProducts = query
    ? products.filter((p) => {
        const queryTerms = query.toLowerCase().split(/\s+/);
        return queryTerms.some(
          (term) =>
            (p.name?.toLowerCase().includes(term) ?? false) ||
            (p.description?.toLowerCase().includes(term) ?? false) ||
            (p.categories?.elements ?? []).some((cat: string) =>
              cat.toLowerCase().includes(term)
            )
        );
      })
    : products;

  const formatPrice = (priceCents?: bigint) => {
    if (!priceCents) return "$0.00";
    const dollars = Number(priceCents) / 100;
    return `$${dollars.toFixed(2)}`;
  };

  const addToCart = (product: (typeof products)[number]) => {
    if (window.parent) {
      window.parent.postMessage(
        {
          type: "prompt",
          payload: {
            prompt: `Add one ${product.name} to my cart 
                    (product ID: ${product.id})`,
          },
        },
        "*"
      );
    }
  };

  if (filteredProducts.length === 0) {
    return (
      <div className="min-h-28 flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <h2 className="text-sm font-bold text-gray-800 mb-1">
            No products found
          </h2>
          <p className="text-xs text-gray-600">
            Try searching for something else
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-2">
      <div className="max-w-4xl mx-auto">
        {query && (
          <div className="mb-2">
            <h1 className="text-sm font-bold text-gray-900">
              "{query}" - {filteredProducts.length} items
            </h1>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
          {filteredProducts.map((product) => (
            <div
              key={product.id ?? ""}
              className="bg-white rounded shadow-sm overflow-hidden
                        hover:shadow-md transition-shadow flex h-32"
            >
              <img
                src={product.picture ?? ""}
                alt={product.name ?? "Product"}
                className="w-32 h-full object-cover flex-none"
              />
              <div className="p-2 flex-1 flex flex-col justify-between">
                <div>
                  <h3
                    className="text-sm font-semibold text-gray-900 mb-1
                              line-clamp-1"
                  >
                    {product.name ?? "Unknown"}
                  </h3>
                  <p className="text-xs text-gray-600 mb-2 line-clamp-2">
                    {product.description ?? ""}
                  </p>
                </div>

                <div className="flex items-end justify-between gap-2">
                  <div>
                    <span className="text-sm font-bold text-gray-900">
                      {formatPrice(product.priceCents)}
                    </span>
                    {product.stockQuantity &&
                      product.stockQuantity > 0n &&
                      product.stockQuantity < 10n && (
                        <div className="text-xs text-orange-600">
                          {String(product.stockQuantity)} left
                        </div>
                      )}
                  </div>

                  <button
                    onClick={() => addToCart(product)}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-3
                              py-1.5 rounded text-xs font-medium
                              transition-colors whitespace-nowrap"
                    disabled={product.stockQuantity === 0n}
                  >
                    {(product.stockQuantity ?? 0n) > 0n
                      ? "Add to Cart"
                      : "Out of Stock"}
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Products;
