export function buildProductLookup(products) {
  return new Map((products || []).map((product) => [product.id, product]));
}

export function calculateCartSubtotal(cartItems, productLookup) {
  return (cartItems || []).reduce((sum, item) => {
    const product = productLookup.get(item.product_id);
    const price = Number(item.unit_price ?? product?.price ?? 0);
    return sum + price * Number(item.quantity || 0);
  }, 0);
}

export function enrichCartItems(cartItems, productLookup) {
  return (cartItems || []).map((item) => ({
    ...item,
    product: productLookup.get(item.product_id) || (
      item.product_name ? { id: item.product_id, name: item.product_name, price: item.unit_price } : null
    ),
  }));
}
