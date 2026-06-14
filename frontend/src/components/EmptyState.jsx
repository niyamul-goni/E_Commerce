export default function EmptyState({ title = 'Nothing here yet', message }) {
  return (
    <div className="state state--empty card">
      <h3>{title}</h3>
      <p>{message || 'There is no data to display right now.'}</p>
    </div>
  );
}
