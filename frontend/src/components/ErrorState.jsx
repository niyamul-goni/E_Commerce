import Button from './Button';

function readableMessage(message) {
  if (typeof message === 'string') return message;
  if (Array.isArray(message)) {
    return message
      .map((item) => item?.msg || item?.message || String(item))
      .filter(Boolean)
      .join(' ');
  }
  if (message && typeof message === 'object') {
    return message.message || message.detail || 'Please try again in a moment.';
  }
  return 'Please try again in a moment.';
}

export default function ErrorState({ title = 'Something went wrong', message, onRetry }) {
  return (
    <div className="state state--error card">
      <h3>{title}</h3>
      <p>{readableMessage(message)}</p>
      {onRetry ? (
        <Button variant="secondary" onClick={onRetry}>
          Retry
        </Button>
      ) : null}
    </div>
  );
}
