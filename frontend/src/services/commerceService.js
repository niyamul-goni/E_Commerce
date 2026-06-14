import { api } from './api';

export async function createOrderRequest(payload) {
  const { data } = await api.post('/orders', payload);
  return data;
}

export async function getMyOrdersRequest() {
  const { data } = await api.get('/orders/me');
  return data;
}

export async function getAllOrdersRequest() {
  const { data } = await api.get('/orders');
  return data;
}

export async function getOrderRequest(orderId) {
  const { data } = await api.get(`/orders/${orderId}`);
  return data;
}

export async function updateOrderStatusRequest(orderId, status) {
  const { data } = await api.put(`/orders/${orderId}/status`, { status });
  return data;
}

export async function addOrderItemRequest(orderId, payload) {
  const { data } = await api.post(`/orders/${orderId}/items`, payload);
  return data;
}

export async function removeOrderItemRequest(orderId, orderItemId) {
  const { data } = await api.delete(`/orders/${orderId}/items/${orderItemId}`);
  return data;
}

export async function recordPaymentRequest(payload) {
  const { data } = await api.post('/payments', payload);
  return data;
}

export async function getPaymentByOrderRequest(orderId) {
  const { data } = await api.get(`/payments/order/${orderId}`);
  return data;
}

export async function createShipmentRequest(payload) {
  const { data } = await api.post('/shipments', payload);
  return data;
}

export async function getShipmentByOrderRequest(orderId) {
  const { data } = await api.get(`/shipments/order/${orderId}`);
  return data;
}

export async function createReviewRequest(payload) {
  const { data } = await api.post('/reviews', payload);
  return data;
}

export async function getReviewsByProductRequest(productId) {
  const { data } = await api.get(`/reviews/product/${productId}`);
  return data;
}

export async function getMyCartItemsRequest() {
  const { data } = await api.get('/cart-items/me');
  return data;
}

export async function addToCartRequest(payload) {
  const { data } = await api.post('/cart-items', payload);
  return data;
}

export async function updateCartItemRequest(cartItemId, payload) {
  const { data } = await api.put(`/cart-items/${cartItemId}`, payload);
  return data;
}

export async function deleteCartItemRequest(cartItemId) {
  const { data } = await api.delete(`/cart-items/${cartItemId}`);
  return data;
}

export async function getDashboardSummaryRequest() {
  const { data } = await api.get('/dashboard/summary');
  return data;
}
