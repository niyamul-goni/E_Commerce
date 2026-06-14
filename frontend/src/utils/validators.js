export function createEmptyErrors() {
  return {};
}

export function validateEmail(value) {
  if (!value) return 'Email is required';
  const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailPattern.test(value) ? '' : 'Enter a valid email address';
}

export function validatePassword(value) {
  if (!value) return 'Password is required';
  if (value.length < 8) return 'Password must be at least 8 characters';
  return '';
}

export function validateRequired(value, label) {
  return value ? '' : `${label} is required`;
}

export function validatePrice(value) {
  if (value === '' || value === null || value === undefined) return 'Price is required';
  return Number(value) > 0 ? '' : 'Price must be greater than 0';
}

export function validateQuantity(value) {
  if (value === '' || value === null || value === undefined) return 'Quantity is required';
  return Number(value) > 0 ? '' : 'Quantity must be at least 1';
}

export function validateRating(value) {
  const numberValue = Number(value);
  if (Number.isNaN(numberValue)) return 'Rating is required';
  if (numberValue < 1 || numberValue > 5) return 'Rating must be between 1 and 5';
  return '';
}
