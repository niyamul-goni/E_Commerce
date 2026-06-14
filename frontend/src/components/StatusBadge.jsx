import { capitalize } from '../utils/format';

export default function StatusBadge({ value }) {
  const status = String(value || 'unknown').toLowerCase();
  return <span className={`status-badge status-badge--${status}`}>{capitalize(status)}</span>;
}
