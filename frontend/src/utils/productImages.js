import { API_BASE_URL } from '../services/api';

// Product images must come from manager uploads. Older seed data used Picsum
// URLs as visual placeholders; treat those as missing instead of presenting
// unrelated photos as real catalog images.

export function isPlaceholderImage(url) {
  const normalized = String(url || '').trim().toLowerCase();
  return !normalized
    || normalized.includes('picsum.photos')
    || normalized.includes('/placeholder');
}

export function resolveProductImage(product, candidateUrl = product?.image_url) {
  if (isPlaceholderImage(candidateUrl)) return null;

  const url = String(candidateUrl).trim();
  if (/^(https?:|data:|blob:)/i.test(url)) return url;

  // Relative /static URLs should follow an explicitly configured remote API.
  // With the default relative /api URL they remain same-origin and are handled
  // by Vite's /static proxy during development.
  if (url.startsWith('/') && /^https?:\/\//i.test(API_BASE_URL)) {
    try {
      return `${new URL(API_BASE_URL).origin}${url}`;
    } catch {
      return url;
    }
  }

  return url;
}

export function resolveProductGallery(product) {
  const gallery = (product?.images || [])
    .map((image) => resolveProductImage(product, image?.image_url))
    .filter(Boolean);

  if (gallery.length) return [...new Set(gallery)];
  const primaryImage = resolveProductImage(product);
  return primaryImage ? [primaryImage] : [];
}
