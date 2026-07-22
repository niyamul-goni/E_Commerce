import { api, API_BASE_URL, getStoredToken } from './api';

// ── Categories ──────────────────────────────────────────────────────────────

export async function getCategoriesRequest() {
  const { data } = await api.get('/categories');
  return data;
}

export async function getManagedCategoriesRequest() {
  const { data } = await api.get('/categories/manage/all');
  return data;
}

export async function createCategoryRequest(payload) {
  const { data } = await api.post('/categories', payload);
  return data;
}

export async function updateCategoryRequest(categoryId, payload) {
  const { data } = await api.put(`/categories/${categoryId}`, payload);
  return data;
}

export async function deleteCategoryRequest(categoryId) {
  const { data } = await api.delete(`/categories/${categoryId}`);
  return data;
}

// ── Subcategories ─────────────────────────────────────────────────────────────

export async function getSubcategoriesRequest(categoryId = null) {
  const params = categoryId ? `?category_id=${categoryId}` : '';
  const { data } = await api.get(`/subcategories${params}`);
  return data;
}

export async function getCategorySubcategoriesRequest(categoryId) {
  const { data } = await api.get(`/categories/${categoryId}/subcategories`);
  return data;
}

// ── Collections ───────────────────────────────────────────────────────────────

export async function getCollectionsRequest() {
  const { data } = await api.get('/collections');
  return data;
}

// ── Suppliers ────────────────────────────────────────────────────────────────

export async function getSuppliersRequest() {
  const { data } = await api.get('/suppliers');
  return data;
}

export async function createSupplierRequest(payload) {
  const { data } = await api.post('/suppliers', payload);
  return data;
}

export async function updateSupplierRequest(supplierId, payload) {
  const { data } = await api.put(`/suppliers/${supplierId}`, payload);
  return data;
}

export async function deleteSupplierRequest(supplierId) {
  const { data } = await api.delete(`/suppliers/${supplierId}`);
  return data;
}

// ── Brands — from the actual `brands` table via /products/brands ─────────────

export async function getBrandsRequest() {
  const { data } = await api.get('/products/brands');
  return data;
}

// ── Products ─────────────────────────────────────────────────────────────────

/**
 * Search/filter products.
 * Supported params: query, category_id, brand_id, supplier_id, size, min_price, max_price, limit
 */
export async function getProductsRequest(params = {}) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      query.set(key, String(value));
    }
  });
  const { data } = await api.get(`/products/search?${query.toString()}`);
  return data;
}

export async function getManagedProductsRequest() {
  const { data } = await api.get('/products/manage/all');
  return data;
}

export async function getProductRequest(productId) {
  const { data } = await api.get(`/products/${productId}`);
  return data;
}

/** Get all active variants for a product (color/size/material/stock). */
export async function getProductVariantsRequest(productId) {
  const { data } = await api.get(`/products/${productId}/variants`);
  return data;
}

export async function createProductRequest(payload) {
  const { data } = await api.post('/products', payload);
  return data;
}

export async function updateProductRequest(productId, payload) {
  const { data } = await api.put(`/products/${productId}`, payload);
  return data;
}

export async function deleteProductRequest(productId) {
  const { data } = await api.delete(`/products/${productId}`);
  return data;
}

/** Upload an image file for a product. */
export async function uploadProductImageRequest(productId, file) {
  const formData = new FormData();
  formData.append('file', file);

  // Use the browser's native multipart handling for file uploads. In
  // particular, never set Content-Type: the browser must append its generated
  // boundary or FastAPI cannot parse the `file` field and responds with 422.
  const token = getStoredToken();
  const response = await fetch(`${API_BASE_URL}/products/${productId}/image`, {
    method: 'POST',
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: formData,
  });

  let payload = null;
  try {
    payload = await response.json();
  } catch {
    // A proxy/server failure may return an empty or non-JSON body.
  }

  if (!response.ok) {
    const detail = payload?.detail;
    const message = typeof detail === 'string'
      ? detail
      : Array.isArray(detail)
        ? detail.map((item) => item?.msg || 'Invalid upload').join(' ')
        : `Image upload failed (${response.status}).`;
    throw new Error(message);
  }

  return payload;
}

// ── Curated Feeds ─────────────────────────────────────────────────────────────

/** Featured products for the homepage hero section */
export async function getFeaturedProductsRequest(limit = 12) {
  const { data } = await api.get(`/products/featured?limit=${limit}`);
  return data;
}

/** Trending products based on popularity flags */
export async function getTrendingProductsRequest(limit = 12) {
  const { data } = await api.get(`/products/trending?limit=${limit}`);
  return data;
}

/** Newest arrivals */
export async function getNewArrivalsRequest(limit = 12) {
  const { data } = await api.get(`/products/new-arrivals?limit=${limit}`);
  return data;
}

/** Top rated products by review average */
export async function getTopRatedProductsRequest(limit = 12) {
  const { data } = await api.get(`/products/top-rated?limit=${limit}`);
  return data;
}

/** Related products (same category/brand) */
export async function getRelatedProductsRequest(productId, limit = 8) {
  const { data } = await api.get(`/products/${productId}/related?limit=${limit}`);
  return data;
}

/** All images for a product */
export async function getProductImagesRequest(productId) {
  const { data } = await api.get(`/products/${productId}/images`);
  return data;
}
