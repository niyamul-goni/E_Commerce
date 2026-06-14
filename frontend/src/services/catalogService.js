import { api } from './api';

export async function getCategoriesRequest() {
  const { data } = await api.get('/categories');
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

export async function getProductsRequest(params = {}) {
  const query = new URLSearchParams();
  const hasFilters = Object.values(params).some((value) => value !== undefined && value !== null && value !== '');

  if (!hasFilters) {
    const { data } = await api.get('/products');
    return data;
  }

  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      query.set(key, value);
    }
  });

  const { data } = await api.get(`/products/search?${query.toString()}`);
  return data;
}

export async function getProductRequest(productId) {
  const { data } = await api.get(`/products/${productId}`);
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
