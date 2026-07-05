export function formatCurrency(value) {
  const num = Number(value || 0);
  return '৳' + new Intl.NumberFormat('en-BD', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(num);
}

export function formatDate(value) {
  if (!value) return 'N/A';
  return new Date(value).toLocaleString('en-IN', {
    dateStyle: 'medium',
    timeStyle: 'short',
  });
}

export function capitalize(value) {
  if (!value) return '';
  return String(value)
    .replaceAll('_', ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase());
}
