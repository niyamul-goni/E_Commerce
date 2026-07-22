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
  return isPlaceholderImage(candidateUrl) ? null : candidateUrl;
}

export function resolveProductGallery(product) {
  const gallery = (product?.images || [])
    .map((image) => image?.image_url)
    .filter((url) => !isPlaceholderImage(url));

  if (gallery.length) return [...new Set(gallery)];
  const primaryImage = resolveProductImage(product);
  return primaryImage ? [primaryImage] : [];
}
