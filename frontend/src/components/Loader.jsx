export default function Loader({ label = 'Loading...' }) {
  return (
    <div className="state state--loading">
      <div className="spinner" />
      <p>{label}</p>
    </div>
  );
}
