import { api } from './api';

// ── Dashboard KPIs ────────────────────────────────────────────────────────────
export async function getManagerKPIsRequest() {
  const { data } = await api.get('/analytics/dashboard/kpis');
  return data;
}

export async function getMonthlyRevenueRequest(months = 12) {
  const { data } = await api.get(`/analytics/revenue/monthly?months=${months}`);
  return data;
}

export async function getBestSellingProductsRequest(limit = 5) {
  const { data } = await api.get(`/analytics/products/best-selling?limit=${limit}`);
  return data;
}

export async function getRevenueByCategoryRequest() {
  const { data } = await api.get('/analytics/revenue/by-category');
  return data;
}

export async function getRevenueByBrandRequest() {
  const { data } = await api.get('/analytics/revenue/by-brand');
  return data;
}

export async function getTopRatedProductsRequest(limit = 10) {
  const { data } = await api.get(`/analytics/products/top-rated?limit=${limit}`);
  return data;
}

export async function getCouponPerformanceRequest() {
  const { data } = await api.get('/analytics/coupons/performance');
  return data;
}

export async function getSupplierPerformanceRequest() {
  const { data } = await api.get('/analytics/suppliers/performance');
  return data;
}

export async function getDailyRevenueRequest(days = 30) {
  const { data } = await api.get(`/analytics/revenue/daily?days=${days}`);
  return data;
}

// ── Manager: Customers ────────────────────────────────────────────────────────
export async function getAllCustomersRequest() {
  const { data } = await api.get('/manager/customers');
  return data;
}

// ── Manager: Inventory ────────────────────────────────────────────────────────
export async function getInventoryLevelsRequest() {
  const { data } = await api.get('/manager/inventory');
  return data;
}

// ── Manager: Reviews moderation ───────────────────────────────────────────────
export async function getAllReviewsRequest() {
  const { data } = await api.get('/manager/reviews');
  return data;
}

export async function replyToReviewRequest(reviewId, replyText) {
  const { data } = await api.post(`/manager/reviews/${reviewId}/reply`, { reply_text: replyText });
  return data;
}

// ── Manager: Returns ──────────────────────────────────────────────────────────
export async function getAllReturnsRequest() {
  const { data } = await api.get('/manager/returns');
  return data;
}

export async function updateReturnStatusRequest(returnId, status) {
  const { data } = await api.put(`/manager/returns/${returnId}/status`, { status });
  return data;
}

// ── Manager: Shipments ────────────────────────────────────────────────────────
export async function updateShipmentRequest(shipmentId, payload) {
  const { data } = await api.put(`/manager/shipments/${shipmentId}`, payload);
  return data;
}

// ── Manager: Coupons ──────────────────────────────────────────────────────────
export async function getCouponsRequest() {
  const { data } = await api.get('/coupons/list');
  return data;
}

export async function createCouponRequest(payload) {
  const { data } = await api.post('/coupons', payload);
  return data;
}

export async function toggleCouponActiveRequest(couponId, isActive) {
  const { data } = await api.put(`/coupons/${couponId}`, { is_active: isActive });
  return data;
}
